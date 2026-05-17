// Package save handles JSON persistence of the pet state.
package save

import (
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/d3ej/netgotchi/internal/pet"
)

const defaultPath = "saves/netgotchi_save.json"

type saveFile struct {
	Pet *pet.Pet `json:"pet"`
}

// Save writes the pet state to disk.
func Save(p *pet.Pet, path string) error {
	if path == "" {
		path = defaultPath
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	enc := json.NewEncoder(f)
	enc.SetIndent("", "  ")
	return enc.Encode(saveFile{Pet: p})
}

// Load reads the pet state from disk.  Returns a fresh pet on any error.
func Load(path string) *pet.Pet {
	if path == "" {
		path = defaultPath
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return pet.New()
	}
	var sf saveFile
	if err := json.Unmarshal(data, &sf); err != nil || sf.Pet == nil {
		return pet.New()
	}
	if sf.Pet.ToolAffinity == nil {
		sf.Pet.ToolAffinity = make(map[string]int)
	}
	return sf.Pet
}

// HasSave returns true if a save file exists.
func HasSave(path string) bool {
	if path == "" {
		path = defaultPath
	}
	_, err := os.Stat(path)
	return err == nil
}

// Delete removes the save file.
func Delete(path string) error {
	if path == "" {
		path = defaultPath
	}
	return os.Remove(path)
}
