-- Roblox 서버에서 VESSL의 Persona API를 호출한다.
-- 이 Script의 PersonaApiUrl 속성에 VESSL HTTP 주소를 입력해야 한다.

local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TextService = game:GetService("TextService")

local REQUEST_COOLDOWN = 2
local MAX_MESSAGE_LENGTH = 500

local remote = ReplicatedStorage:FindFirstChild("PersonaChatEvent")
if not remote then
	remote = Instance.new("RemoteEvent")
	remote.Name = "PersonaChatEvent"
	remote.Parent = ReplicatedStorage
end

local conversations = {}
local busy = {}
local lastRequestAt = {}

local function sendError(player, message)
	remote:FireClient(player, {
		kind = "error",
		text = message,
	})
end

local function getApiEndpoint()
	local baseUrl = script:GetAttribute("PersonaApiUrl")
	if type(baseUrl) ~= "string" then
		return nil
	end

	baseUrl = baseUrl:match("^%s*(.-)%s*$"):gsub("/+$", "")
	local isSecure = baseUrl:match("^https://") ~= nil
	local isLocalStudio = RunService:IsStudio()
		and baseUrl:match("^http://127%.0%.0%.1[:/]") ~= nil
	if not isSecure and not isLocalStudio then
		return nil
	end

	return baseUrl .. "/api/chat"
end

local function normalizeMessage(value)
	if type(value) ~= "string" then
		return nil
	end

	local message = value:match("^%s*(.-)%s*$")
	local characterCount = utf8.len(message)
	if not characterCount or characterCount < 1 or characterCount > MAX_MESSAGE_LENGTH then
		return nil
	end

	return message
end

local function filterForPlayer(player, text)
	-- 외부 서버에서 받은 문장도 화면에 표시하기 전에 Roblox 필터를 통과시킨다.
	local ok, filteredText = pcall(function()
		local result = TextService:FilterStringAsync(
			text,
			player.UserId,
			Enum.TextFilterContext.PrivateChat
		)
		return result:GetNonChatStringForUserAsync(player.UserId)
	end)

	if not ok or filteredText == "" then
		return nil
	end
	return filteredText
end

local function requestReply(player, message)
	local endpoint = getApiEndpoint()
	if not endpoint then
		sendError(player, "서버에 PersonaApiUrl을 설정해 주세요.")
		return
	end

	local state = conversations[player] or {
		intro = "",
		messages = {},
	}
	local body = HttpService:JSONEncode({
		message = message,
		state = state,
	})

	local requestOk, response = pcall(function()
		return HttpService:RequestAsync({
			Url = endpoint,
			Method = "POST",
			Headers = {
				["Content-Type"] = "application/json",
			},
			Body = body,
		})
	end)

	if not requestOk or not response.Success then
		warn("Persona API request failed", requestOk and response.StatusCode or response)
		sendError(player, "세종의 답변을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")
		return
	end

	local decodeOk, payload = pcall(HttpService.JSONDecode, HttpService, response.Body)
	if not decodeOk or type(payload) ~= "table" or type(payload.reply) ~= "string"
		or type(payload.state) ~= "table" then
		warn("Persona API returned an invalid response")
		sendError(player, "서버 응답 형식이 올바르지 않습니다.")
		return
	end

	local filteredReply = filterForPlayer(player, payload.reply)
	if not filteredReply then
		sendError(player, "답변을 안전하게 표시하지 못했습니다.")
		return
	end

	conversations[player] = payload.state
	remote:FireClient(player, {
		kind = "reply",
		text = filteredReply,
	})
end

remote.OnServerEvent:Connect(function(player, rawMessage)
	local message = normalizeMessage(rawMessage)
	if not message then
		sendError(player, "메시지는 1~500자로 입력해 주세요.")
		return
	end

	local now = os.clock()
	if busy[player] or now - (lastRequestAt[player] or 0) < REQUEST_COOLDOWN then
		sendError(player, "답변을 기다린 뒤 다시 보내 주세요.")
		return
	end

	busy[player] = true
	lastRequestAt[player] = now
	local ok, errorMessage = pcall(requestReply, player, message)
	busy[player] = nil

	if not ok then
		warn("Persona chat failed", errorMessage)
		sendError(player, "대화를 처리하지 못했습니다.")
	end
end)

Players.PlayerRemoving:Connect(function(player)
	conversations[player] = nil
	busy[player] = nil
	lastRequestAt[player] = nil
end)
