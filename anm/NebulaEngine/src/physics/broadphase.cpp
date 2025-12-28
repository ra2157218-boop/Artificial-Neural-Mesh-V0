#include "broadphase.h"
#include "../ecs/registry.h"
#include <unordered_map>
#include <algorithm>

namespace ne {

std::vector<Broadphase::Pair> Broadphase::find_pairs(const Registry& reg, float cell_size) {
    std::vector<Pair> pairs;
    
    // Group entities by grid cell
    std::unordered_map<CellKey, std::vector<Entity>, CellKeyHash> grid;
    
    const auto& alive = reg.alive();
    
    // Insert entities into grid cells
    for (Entity e : alive) {
        if (!reg.has_alive(e)) continue;
        if (!reg.has_sphere(e) && !reg.has_aabb(e)) continue; // Skip entities without collision shapes
        
        const auto& t = reg.transform(e);
        
        // Calculate grid cell coordinates
        CellKey cell;
        cell.x = static_cast<int>(std::floor(t.pos.x / cell_size));
        cell.y = static_cast<int>(std::floor(t.pos.y / cell_size));
        cell.z = static_cast<int>(std::floor(t.pos.z / cell_size));
        
        grid[cell].push_back(e);
    }
    
    // Check pairs within same cell and neighboring cells
    // For simplicity, check all entities in same cell and adjacent cells
    for (const auto& [cell, entities] : grid) {
        // Pairs within same cell
        for (size_t i = 0; i < entities.size(); ++i) {
            for (size_t j = i + 1; j < entities.size(); ++j) {
                pairs.push_back({entities[i], entities[j]});
            }
        }
        
        // Check adjacent cells (simplified: check +1 in each direction)
        for (int dx = 0; dx <= 1; ++dx) {
            for (int dy = 0; dy <= 1; ++dy) {
                for (int dz = 0; dz <= 1; ++dz) {
                    if (dx == 0 && dy == 0 && dz == 0) continue; // Skip same cell
                    
                    CellKey neighbor{cell.x + dx, cell.y + dy, cell.z + dz};
                    auto it = grid.find(neighbor);
                    if (it != grid.end()) {
                        // Check pairs between this cell and neighbor
                        for (Entity e1 : entities) {
                            for (Entity e2 : it->second) {
                                if (e1 < e2) { // Avoid duplicates
                                    pairs.push_back({e1, e2});
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Remove duplicates (simple approach: sort and unique)
    std::sort(pairs.begin(), pairs.end());
    pairs.erase(std::unique(pairs.begin(), pairs.end()), pairs.end());
    
    return pairs;
}

} // namespace ne
