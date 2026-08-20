package save

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/d3ej/netgotchi/internal/pet"
)

func TestSaveLoadRoundTrip(t *testing.T) {
	path := filepath.Join(t.TempDir(), "sub", "save.json")

	p := pet.New()
	p.EarnXP(150, "ping")
	p.Name = "Roundtrip"

	if err := Save(p, path); err != nil {
		t.Fatalf("Save() error = %v", err)
	}

	loaded := Load(path)

	if loaded.Name != "Roundtrip" {
		t.Errorf("Name = %q, want Roundtrip", loaded.Name)
	}
	if loaded.XP != 150 {
		t.Errorf("XP = %d, want 150", loaded.XP)
	}
	if loaded.ToolAffinity["ping"] != 1 {
		t.Errorf("ToolAffinity[ping] = %d, want 1", loaded.ToolAffinity["ping"])
	}
}

func TestLoadMissingFileReturnsFreshPet(t *testing.T) {
	path := filepath.Join(t.TempDir(), "does-not-exist.json")

	p := Load(path)

	if p.Stage != pet.StageEgg {
		t.Errorf("Stage = %v, want StageEgg for a fresh pet", p.Stage)
	}
	if p.ToolAffinity == nil {
		t.Error("ToolAffinity is nil, want an initialized map")
	}
}

func TestLoadCorruptFileReturnsFreshPet(t *testing.T) {
	path := filepath.Join(t.TempDir(), "corrupt.json")
	if err := os.WriteFile(path, []byte("not json"), 0o644); err != nil {
		t.Fatalf("failed to write fixture: %v", err)
	}

	p := Load(path)

	if p.Stage != pet.StageEgg {
		t.Errorf("Stage = %v, want StageEgg for a fresh pet on corrupt save", p.Stage)
	}
}

func TestHasSaveAndDelete(t *testing.T) {
	path := filepath.Join(t.TempDir(), "save.json")

	if HasSave(path) {
		t.Error("HasSave() = true before any save exists")
	}

	if err := Save(pet.New(), path); err != nil {
		t.Fatalf("Save() error = %v", err)
	}
	if !HasSave(path) {
		t.Error("HasSave() = false after saving")
	}

	if err := Delete(path); err != nil {
		t.Fatalf("Delete() error = %v", err)
	}
	if HasSave(path) {
		t.Error("HasSave() = true after Delete")
	}
}
