-- 플레이어의 질문을 서버로 보내고 세종 NPC 머리 위에 답변 말풍선을 띄운다.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TextChatService = game:GetService("TextChatService")
local Players = game:GetService("Players")

local NPC_NAME = "Sejong"
local MAX_BUBBLE_LENGTH = 240

local player = Players.LocalPlayer
local remote = ReplicatedStorage:WaitForChild("PersonaChatEvent")

local screenGui = Instance.new("ScreenGui")
screenGui.Name = "PersonaChatGui"
screenGui.ResetOnSpawn = false
screenGui.Parent = player:WaitForChild("PlayerGui")

local panel = Instance.new("Frame")
panel.Name = "Panel"
panel.AnchorPoint = Vector2.new(0.5, 1)
panel.Position = UDim2.new(0.5, 0, 1, -28)
panel.Size = UDim2.new(0, 520, 0, 190)
panel.BackgroundColor3 = Color3.fromRGB(245, 244, 239)
panel.BorderSizePixel = 0
panel.Parent = screenGui

local panelCorner = Instance.new("UICorner")
panelCorner.CornerRadius = UDim.new(0, 8)
panelCorner.Parent = panel

local title = Instance.new("TextLabel")
title.Position = UDim2.fromOffset(18, 12)
title.Size = UDim2.new(1, -36, 0, 24)
title.BackgroundTransparency = 1
title.Font = Enum.Font.GothamBold
title.Text = "세종과의 대화"
title.TextColor3 = Color3.fromRGB(42, 49, 46)
title.TextSize = 18
title.TextXAlignment = Enum.TextXAlignment.Left
title.Parent = panel

local answer = Instance.new("TextLabel")
answer.Position = UDim2.fromOffset(18, 42)
answer.Size = UDim2.new(1, -36, 0, 78)
answer.BackgroundTransparency = 1
answer.Font = Enum.Font.Gotham
answer.Text = "세종에게 질문해 보세요."
answer.TextColor3 = Color3.fromRGB(70, 76, 73)
answer.TextSize = 15
answer.TextWrapped = true
answer.TextXAlignment = Enum.TextXAlignment.Left
answer.TextYAlignment = Enum.TextYAlignment.Top
answer.Parent = panel

local input = Instance.new("TextBox")
input.Position = UDim2.new(0, 18, 1, -54)
input.Size = UDim2.new(1, -126, 0, 38)
input.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
input.BorderSizePixel = 0
input.ClearTextOnFocus = false
input.Font = Enum.Font.Gotham
input.PlaceholderText = "전하께 말을 건네 보세요"
input.Text = ""
input.TextColor3 = Color3.fromRGB(35, 39, 37)
input.TextSize = 15
input.TextXAlignment = Enum.TextXAlignment.Left
input.Parent = panel

local inputCorner = Instance.new("UICorner")
inputCorner.CornerRadius = UDim.new(0, 6)
inputCorner.Parent = input

local inputPadding = Instance.new("UIPadding")
inputPadding.PaddingLeft = UDim.new(0, 12)
inputPadding.PaddingRight = UDim.new(0, 12)
inputPadding.Parent = input

local sendButton = Instance.new("TextButton")
sendButton.Position = UDim2.new(1, -98, 1, -54)
sendButton.Size = UDim2.fromOffset(80, 38)
sendButton.BackgroundColor3 = Color3.fromRGB(40, 91, 67)
sendButton.BorderSizePixel = 0
sendButton.Font = Enum.Font.GothamBold
sendButton.Text = "보내기"
sendButton.TextColor3 = Color3.fromRGB(255, 255, 255)
sendButton.TextSize = 14
sendButton.Parent = panel

local buttonCorner = Instance.new("UICorner")
buttonCorner.CornerRadius = UDim.new(0, 6)
buttonCorner.Parent = sendButton

local waiting = false

local function setWaiting(value)
	waiting = value
	input.TextEditable = not value
	sendButton.Active = not value
	sendButton.AutoButtonColor = not value
	sendButton.Text = value and "대기 중" or "보내기"
end

local function showNpcBubble(text)
	local npc = workspace:FindFirstChild(NPC_NAME)
	local head = npc and npc:FindFirstChild("Head")
	if not head or not head:IsA("BasePart") then
		answer.Text = text .. "\n\n[Workspace에서 Sejong NPC의 Head를 찾지 못했습니다.]"
		return
	end

	local bubbleText = text
	if utf8.len(text) and utf8.len(text) > MAX_BUBBLE_LENGTH then
		local byteOffset = utf8.offset(text, MAX_BUBBLE_LENGTH + 1)
		bubbleText = string.sub(text, 1, byteOffset - 1) .. "..."
	end
	TextChatService:DisplayBubble(head, bubbleText)
end

local function submit()
	if waiting then
		return
	end

	local message = input.Text:match("^%s*(.-)%s*$")
	if message == "" then
		return
	end

	setWaiting(true)
	answer.Text = "답변을 기다리고 있습니다."
	input.Text = ""
	remote:FireServer(message)
end

sendButton.Activated:Connect(submit)
input.FocusLost:Connect(function(enterPressed)
	if enterPressed then
		submit()
	end
end)

remote.OnClientEvent:Connect(function(payload)
	setWaiting(false)
	if type(payload) ~= "table" or type(payload.text) ~= "string" then
		answer.Text = "올바르지 않은 응답을 받았습니다."
		return
	end

	answer.Text = payload.text
	if payload.kind == "reply" then
		showNpcBubble(payload.text)
	end
end)
