-- 실습 프로젝트에 바닥이나 Sejong 모델이 없으면 기본 장면을 자동으로 만든다.

if not workspace:FindFirstChild("SejongGround") then
	local ground = Instance.new("Part")
	ground.Name = "SejongGround"
	ground.Size = Vector3.new(120, 1, 120)
	ground.Position = Vector3.new(0, -0.5, 0)
	ground.Color = Color3.fromRGB(72, 101, 73)
	ground.Material = Enum.Material.Grass
	ground.Anchored = true
	ground.CanCollide = true
	ground.TopSurface = Enum.SurfaceType.Smooth
	ground.BottomSurface = Enum.SurfaceType.Smooth
	ground.Parent = workspace
end

if not workspace:FindFirstChildWhichIsA("SpawnLocation") then
	local spawn = Instance.new("SpawnLocation")
	spawn.Name = "SejongSpawn"
	spawn.Size = Vector3.new(8, 1, 8)
	spawn.Position = Vector3.new(0, 0.5, 14)
	spawn.Anchored = true
	spawn.Neutral = true
	spawn.Duration = 0
	spawn.Parent = workspace
end

if workspace:FindFirstChild("Sejong") then
	return
end

local model = Instance.new("Model")
model.Name = "Sejong"

local function makePart(name, size, position, color)
	local part = Instance.new("Part")
	part.Name = name
	part.Size = size
	part.Position = position
	part.Color = color
	part.Anchored = true
	part.CanCollide = name ~= "Head"
	part.Parent = model
	return part
end

local robe = Color3.fromRGB(145, 22, 34)
local skin = Color3.fromRGB(218, 183, 148)

local torso = makePart("Torso", Vector3.new(4.8, 4.6, 2.2), Vector3.new(8, 4.3, 0), robe)
local head = makePart("Head", Vector3.new(2.6, 2.6, 2.6), Vector3.new(8, 8, 0), skin)
makePart("LeftArm", Vector3.new(1.2, 4.4, 1.5), Vector3.new(4.9, 4.4, 0), robe)
makePart("RightArm", Vector3.new(1.2, 4.4, 1.5), Vector3.new(11.1, 4.4, 0), robe)
makePart("LeftLeg", Vector3.new(1.8, 2.6, 1.8), Vector3.new(6.8, 0.8, 0), Color3.fromRGB(25, 28, 31))
makePart("RightLeg", Vector3.new(1.8, 2.6, 1.8), Vector3.new(9.2, 0.8, 0), Color3.fromRGB(25, 28, 31))

local hat = makePart("Hat", Vector3.new(3.3, 1.0, 3.0), Vector3.new(8, 9.7, 0), Color3.fromRGB(17, 19, 22))
hat.CanCollide = false

local badge = makePart("RoyalBadge", Vector3.new(1.1, 1.2, 0.15), Vector3.new(8, 4.7, -1.18), Color3.fromRGB(213, 179, 65))
badge.CanCollide = false

local face = Instance.new("Decal")
face.Name = "Face"
face.Texture = "rbxasset://textures/face.png"
face.Face = Enum.NormalId.Front
face.Parent = head

local humanoid = Instance.new("Humanoid")
humanoid.DisplayName = "세종"
humanoid.Parent = model

model.PrimaryPart = torso
model.Parent = workspace
