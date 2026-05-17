// Package pet provides the virtual pet model, evolution logic, and ASCII art
// sprites for each evolution stage.
package pet

// Sprite is a multi-line ASCII art string for a pet evolution stage.
type Sprite struct {
	Lines []string
}

// Sprites maps stage → animation → Sprite.
var Sprites = map[Stage]map[string]Sprite{
	StageEgg: {
		"idle": {Lines: []string{
			"  .---.  ",
			" ( o o ) ",
			"  `---'  ",
		}},
		"wobble": {Lines: []string{
			"  .---.  ",
			" ( O O ) ",
			"  `---'  ",
		}},
	},
	StageHatchling: {
		"idle": {Lines: []string{
			"  .---.  ",
			" (^_^;)  ",
			"  /| |\\  ",
		}},
		"happy": {Lines: []string{
			"  .---.  ",
			" (^‿^)   ",
			"  \\|_|/  ",
		}},
		"sad": {Lines: []string{
			"  .---.  ",
			" (;__;)  ",
			"  /| |\\  ",
		}},
	},
	StageJuvenile: {
		"idle": {Lines: []string{
			" .-----. ",
			"(>-_-< ) ",
			"/|| ||\\ ",
			"         ",
		}},
		"happy": {Lines: []string{
			" .-----. ",
			"(>^‿^< ) ",
			"\\||_||/ ",
			"         ",
		}},
	},
	StageAdult: {
		"idle": {Lines: []string{
			"  ╔═══╗  ",
			"  ║>_<║  ",
			"  ╠═══╣  ",
			"  ╚═╤═╝  ",
			"   /│\\   ",
		}},
		"happy": {Lines: []string{
			"  ╔═══╗  ",
			"  ║^‿^║  ",
			"  ╠═══╣  ",
			"  ╚═╤═╝  ",
			"   \\│/   ",
		}},
	},
	StageElder: {
		"idle": {Lines: []string{
			" ┌─────┐ ",
			" │ ◈_◈ │ ",
			" ├─────┤ ",
			" │ ═╬═ │ ",
			" └──┬──┘ ",
			"   /│\\   ",
		}},
		"happy": {Lines: []string{
			" ┌─────┐ ",
			" │ ◈‿◈ │ ",
			" ├─────┤ ",
			" │ ═╬═ │ ",
			" └──┬──┘ ",
			"   \\│/   ",
		}},
	},
}

// GetSprite returns the sprite for the given stage and animation name,
// falling back to "idle" if the animation is not found.
func GetSprite(stage Stage, anim string) Sprite {
	stageSprites, ok := Sprites[stage]
	if !ok {
		stageSprites = Sprites[StageEgg]
	}
	s, ok := stageSprites[anim]
	if !ok {
		s = stageSprites["idle"]
	}
	return s
}
