package pet

import "testing"

func TestNew(t *testing.T) {
	p := New()
	if p.Stage != StageEgg {
		t.Errorf("Stage = %v, want StageEgg", p.Stage)
	}
	if p.Level != 1 {
		t.Errorf("Level = %d, want 1", p.Level)
	}
	if p.ToolAffinity == nil {
		t.Error("ToolAffinity map is nil")
	}
}

func TestUpdateDecay(t *testing.T) {
	p := New()
	p.Hunger = 50
	p.Energy = 50

	p.Update(3600) // one hour

	if p.Hunger != 49 {
		t.Errorf("Hunger = %v, want 49 after 1hr decay", p.Hunger)
	}
	if p.Energy != 49 {
		t.Errorf("Energy = %v, want 49 after 1hr decay", p.Energy)
	}
}

func TestUpdateClampsAtZero(t *testing.T) {
	p := New()
	p.Hunger = 0.5
	p.Energy = 0.5

	p.Update(3600)

	if p.Hunger != 0 {
		t.Errorf("Hunger = %v, want clamped to 0", p.Hunger)
	}
	if p.Energy != 0 {
		t.Errorf("Energy = %v, want clamped to 0", p.Energy)
	}
}

func TestFeed(t *testing.T) {
	p := New()
	p.Hunger = 50
	p.Mood = 50

	p.Feed(20)

	if p.Hunger != 70 {
		t.Errorf("Hunger = %v, want 70", p.Hunger)
	}
	if p.Mood != 56 {
		t.Errorf("Mood = %v, want 56", p.Mood)
	}
}

func TestFeedClampsAtHundred(t *testing.T) {
	p := New()
	p.Hunger = 95

	p.Feed(20)

	if p.Hunger != 100 {
		t.Errorf("Hunger = %v, want clamped to 100", p.Hunger)
	}
}

func TestEarnXPTracksAffinityAndLevel(t *testing.T) {
	p := New()

	p.EarnXP(150, "ping")

	if p.XP != 150 {
		t.Errorf("XP = %d, want 150", p.XP)
	}
	if p.Level != 2 {
		t.Errorf("Level = %d, want 2", p.Level)
	}
	if p.ToolAffinity["ping"] != 1 {
		t.Errorf("ToolAffinity[ping] = %d, want 1", p.ToolAffinity["ping"])
	}
}

func TestEarnXPEvolves(t *testing.T) {
	p := New()

	evolved := p.EarnXP(100, "ping")

	if !evolved {
		t.Fatal("expected evolution at 100 XP")
	}
	if p.Stage != StageHatchling {
		t.Errorf("Stage = %v, want StageHatchling", p.Stage)
	}
	if p.Name != "Byte" {
		t.Errorf("Name = %q, want Byte", p.Name)
	}
}

func TestEarnXPSkipsIntermediateStages(t *testing.T) {
	p := New()

	// Jump straight past Hatchling and Juvenile to Adult in one award.
	p.EarnXP(900, "nmap")

	if p.Stage != StageAdult {
		t.Errorf("Stage = %v, want StageAdult", p.Stage)
	}
}

func TestEarnXPNoAffinityForEmptyTool(t *testing.T) {
	p := New()
	p.EarnXP(10, "")
	if len(p.ToolAffinity) != 0 {
		t.Errorf("ToolAffinity = %v, want empty", p.ToolAffinity)
	}
}

func TestRest(t *testing.T) {
	p := New()
	p.Energy = 50

	p.Rest()

	if p.Energy != 80 {
		t.Errorf("Energy = %v, want 80", p.Energy)
	}
}

func TestIsHungryAndIsTired(t *testing.T) {
	p := New()
	p.Hunger = 29
	p.Energy = 19

	if !p.IsHungry() {
		t.Error("expected IsHungry() = true at hunger 29")
	}
	if !p.IsTired() {
		t.Error("expected IsTired() = true at energy 19")
	}
}

func TestXPToNext(t *testing.T) {
	p := New()
	p.XP = 50

	cur, needed := p.XPToNext()

	if cur != 50 {
		t.Errorf("cur = %d, want 50", cur)
	}
	if needed != 100 {
		t.Errorf("needed = %d, want 100", needed)
	}
}

func TestXPToNextAtMaxStage(t *testing.T) {
	p := New()
	p.XP = 5000
	p.checkEvolution()

	cur, needed := p.XPToNext()

	if cur != 5000 {
		t.Errorf("cur = %d, want 5000", cur)
	}
	if needed != evolutionXP[StageElder] {
		t.Errorf("needed = %d, want %d", needed, evolutionXP[StageElder])
	}
}

func TestReactToPing(t *testing.T) {
	p := New()
	p.Mood = 50

	p.ReactToPing(true, 5)
	if p.TotalPings != 1 {
		t.Errorf("TotalPings = %d, want 1", p.TotalPings)
	}
	if p.Mood != 55 {
		t.Errorf("Mood = %v, want 55 (fast successful ping)", p.Mood)
	}

	p.Mood = 50
	p.ReactToPing(false, 0)
	if p.Mood != 45 {
		t.Errorf("Mood = %v, want 45 after failed ping", p.Mood)
	}
}

func TestReactToScan(t *testing.T) {
	p := New()
	p.Hunger = 50

	p.ReactToScan(2)

	if p.TotalScans != 1 {
		t.Errorf("TotalScans = %d, want 1", p.TotalScans)
	}
	if p.TotalHostsFound != 2 {
		t.Errorf("TotalHostsFound = %d, want 2", p.TotalHostsFound)
	}
	if p.XP != 20 {
		t.Errorf("XP = %d, want 20", p.XP)
	}
}

func TestReactToScanNoHostsAwardsNothing(t *testing.T) {
	p := New()

	p.ReactToScan(0)

	if p.XP != 0 {
		t.Errorf("XP = %d, want 0 when no hosts found", p.XP)
	}
}

func TestMoodName(t *testing.T) {
	cases := []struct {
		mood float64
		want string
	}{
		{90, "ecstatic"},
		{70, "happy"},
		{50, "neutral"},
		{25, "sad"},
		{5, "miserable"},
	}
	for _, c := range cases {
		if got := MoodName(c.mood); got != c.want {
			t.Errorf("MoodName(%v) = %q, want %q", c.mood, got, c.want)
		}
	}
}
