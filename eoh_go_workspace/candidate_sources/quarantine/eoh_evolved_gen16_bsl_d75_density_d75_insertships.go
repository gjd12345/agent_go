func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
    type cand struct {
        idx     int
        score   float64
        delta   float64
        success bool
    }
    for shipIDOffset, ori := range oris {
        des := dess[shipIDOffset]
        shipID := total_ship + shipIDOffset
        candidates := make([]cand, 0, dispatch.AssignsLen+1)
        for i := 0; i < dispatch.AssignsLen; i++ {
            oldCost := dispatch.Assigns[i].Cost
            ok := dispatch.Assigns[i].AddShip(shipID, ori, des)
            if ok {
                dispatch.Assigns[i].GenRoute()
                newCost := dispatch.Assigns[i].Cost
                if newCost >= 0 {
                    delta := newCost - oldCost
                    candidates = append(candidates, cand{idx: i, delta: delta, score: delta, success: true})
                }
            }
            dispatch.Assigns[i].RemoveShip(shipID)
            dispatch.Assigns[i].GenRoute()
        }
        if len(candidates) > 0 {
            sort.SliceStable(candidates, func(a, b int) bool {
                if candidates[a].score != candidates[b].score {
                    return candidates[a].score < candidates[b].score
                }
                return candidates[a].delta < candidates[b].delta
            })
            chosen := candidates[0]
            dispatch.Assigns[chosen.idx].AddShip(shipID, ori, des)
            dispatch.Assigns[chosen.idx].GenRoute()
        } else {
            created := false
            for i := 0; i < dispatch.AssignsLen; i++ {
                ok := dispatch.Assigns[i].AddShip(shipID, ori, des)
                if ok {
                    dispatch.Assigns[i].GenRoute()
                    if dispatch.Assigns[i].Cost >= 0 {
                        created = true
                        break
                    } else {
                        dispatch.Assigns[i].RemoveShip(shipID)
                        dispatch.Assigns[i].GenRoute()
                    }
                }
            }
            if !created && dispatch.AssignsLen < MAXASSIGNS {
                dispatch.Assigns[dispatch.AssignsLen].AddShip(shipID, ori, des)
                dispatch.Assigns[dispatch.AssignsLen].GenRoute()
                if dispatch.Assigns[dispatch.AssignsLen].Cost >= 0 {
                    dispatch.AssignsLen++
                    created = true
                } else {
                    dispatch.Assigns[dispatch.AssignsLen].RemoveShip(shipID)
                    dispatch.Assigns[dispatch.AssignsLen].GenRoute()
                }
            }
            if !created && dispatch.AssignsLen < MAXASSIGNS {
                dispatch.AssignsLen++
                dispatch.Assigns[dispatch.AssignsLen-1].AddShip(shipID, ori, des)
                dispatch.Assigns[dispatch.AssignsLen-1].GenRoute()
            }
        }
    }
    dispatch.RenewnTotalCost()
    return dispatch
}