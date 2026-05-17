package pet

import (
	"math"
	"time"
)

// Stage is the pet's current evolution stage.
type Stage int

const (
	StageEgg Stage = iota
	StageHatchling
	StageJuvenile
	StageAdult
	StageElder
)

// stageOrder is used for evolution comparisons.
var stageOrder = []Stage{StageEgg, StageHatchling, StageJuvenile, StageAdult, StageElder}

// StageNames maps each stage to its display name.
var StageNames = map[Stage]string{
	StageEgg:       "Bit",
	StageHatchling: "Byte",
	StageJuvenile:  "Packet",
	StageAdult:     "Frame",
	StageElder:     "Stream",
}

// StageTitles maps each stage to the stage tier name (shown in parentheses).
var StageTitles = map[Stage]string{
	StageEgg:       "Egg",
	StageHatchling: "Hatchling",
	StageJuvenile:  "Juvenile",
	StageAdult:     "Adult",
	StageElder:     "Elder",
}

// evolutionXP is the XP threshold required to reach each stage.
var evolutionXP = map[Stage]int{
	StageEgg:       0,
	StageHatchling: 100,
	StageJuvenile:  300,
	StageAdult:     900,
	StageElder:     4500,
}

// MoodName returns a descriptive mood string.
func MoodName(mood float64) string {
	switch {
	case mood >= 80:
		return "ecstatic"
	case mood >= 60:
		return "happy"
	case mood >= 40:
		return "neutral"
	case mood >= 20:
		return "sad"
	default:
		return "miserable"
	}
}

// Pet is the NetGotchi virtual pet.
type Pet struct {
	Name            string         `json:"name"`
	Stage           Stage          `json:"stage"`
	Mood            float64        `json:"mood"`
	Hunger          float64        `json:"hunger"`
	Energy          float64        `json:"energy"`
	XP              int            `json:"xp"`
	Level           int            `json:"level"`
	ToolAffinity    map[string]int `json:"tool_affinity"`
	TotalScans      int            `json:"total_scans"`
	TotalPings      int            `json:"total_pings"`
	TotalHostsFound int            `json:"total_hosts_found"`
	LastUpdate      time.Time      `json:"last_update"`
	LastFed         time.Time      `json:"last_fed"`
}

// New creates a fresh pet at the egg stage.
func New() *Pet {
	now := time.Now()
	return &Pet{
		Name:         "Bit",
		Stage:        StageEgg,
		Mood:         80,
		Hunger:       80,
		Energy:       100,
		Level:        1,
		ToolAffinity: make(map[string]int),
		LastUpdate:   now,
		LastFed:      now,
	}
}

func clamp(v, lo, hi float64) float64 {
	return math.Max(lo, math.Min(hi, v))
}

// Update applies real-time stat decay. Call with the number of seconds elapsed
// since the last update.
func (p *Pet) Update(elapsedSec float64) {
	// 1 point per hour = 1/3600 per second
	decay := elapsedSec / 3600.0
	p.Hunger = clamp(p.Hunger-decay, 0, 100)
	p.Energy = clamp(p.Energy-decay, 0, 100)

	// Mood drifts slowly toward a target influenced by hunger and energy.
	target := p.Hunger*0.4 + p.Energy*0.3 + p.Mood*0.3
	p.Mood = clamp(p.Mood+(target-p.Mood)*0.01, 0, 100)

	p.LastUpdate = time.Now()
	p.checkEvolution()
}

// Feed restores hunger (and a little mood).
func (p *Pet) Feed(foodValue float64) {
	p.Hunger = clamp(p.Hunger+foodValue, 0, 100)
	p.Mood = clamp(p.Mood+foodValue*0.3, 0, 100)
	p.LastFed = time.Now()
}

// EarnXP awards XP, increments tool affinity, and checks for evolution.
// Returns true if the pet evolved.
func (p *Pet) EarnXP(amount int, toolName string) bool {
	p.XP += amount
	p.Level = 1 + p.XP/100
	if toolName != "" {
		p.ToolAffinity[toolName]++
	}
	p.Mood = clamp(p.Mood+float64(amount)*0.2, 0, 100)
	p.Energy = clamp(p.Energy-2, 0, 100)
	return p.checkEvolution()
}

// Rest restores energy.
func (p *Pet) Rest() {
	p.Energy = clamp(p.Energy+30, 0, 100)
}

// ReactToPing updates stats in response to a ping result.
func (p *Pet) ReactToPing(success bool, rttMS float64) {
	p.TotalPings++
	if success {
		p.Mood = clamp(p.Mood+2, 0, 100)
		if rttMS > 0 && rttMS < 10 {
			p.Mood = clamp(p.Mood+3, 0, 100)
		}
	} else {
		p.Mood = clamp(p.Mood-5, 0, 100)
	}
}

// ReactToScan updates stats in response to an nmap scan result.
func (p *Pet) ReactToScan(hostsFound int) {
	p.TotalScans++
	p.TotalHostsFound += hostsFound
	if hostsFound > 0 {
		p.Feed(float64(hostsFound) * 5)
		p.EarnXP(hostsFound*10, "nmap")
	}
}

// IsHungry returns true when hunger is critically low.
func (p *Pet) IsHungry() bool { return p.Hunger < 30 }

// IsTired returns true when energy is critically low.
func (p *Pet) IsTired() bool { return p.Energy < 20 }

// XPToNext returns the XP needed to reach the next evolution stage.
func (p *Pet) XPToNext() (current, needed int) {
	current = p.XP
	for _, s := range stageOrder {
		if evolutionXP[s] > p.XP {
			return current, evolutionXP[s]
		}
	}
	return current, evolutionXP[StageElder]
}

// checkEvolution promotes the pet if it has enough XP.
func (p *Pet) checkEvolution() bool {
	for i := len(stageOrder) - 1; i >= 0; i-- {
		s := stageOrder[i]
		if p.XP >= evolutionXP[s] && int(s) > int(p.Stage) {
			p.Stage = s
			p.Name = StageNames[s]
			return true
		}
	}
	return false
}
