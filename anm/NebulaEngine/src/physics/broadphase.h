#pragma once
#include <vector>
#include <utility>
#include "../core/types.h"

namespace ne {

class Registry;

// Simple spatial grid broadphase for M1
// Partitions space into grid cells to quickly find potential collision pairs
struct Broadphase {
    // Pair of potentially colliding entities
    using Pair = std::pair<Entity, Entity>;
    
    // Find potential collision pairs using spatial grid
    // Returns list of entity pairs that might be colliding
    static std::vector<Pair> find_pairs(const Registry& reg, float cell_size = 2.0f);
    
private:
    // Hash function for grid cell coordinates
    struct CellKey {
        int x, y, z;
        bool operator==(const CellKey& o) const { return x == o.x && y == o.y && z == o.z; }
    };
    
    struct CellKeyHash {
        std::size_t operator()(const CellKey& k) const {
            // Simple hash combining x, y, z
            return std::hash<int>()(k.x) ^ (std::hash<int>()(k.y) << 1) ^ (std::hash<int>()(k.z) << 2);
        }
    };
};

} // namespace ne
