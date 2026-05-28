func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
	orderCount := len(oris)
	seedAssignIdx := dispatch.AssignsLen
	for orderIdx := 0; orderIdx < orderCount; orderIdx++ {
		shipId := total_ship + orderIdx
		ori := oris[orderIdx]
		des := dess[orderIdx]
		bestAssignIdx := -1
		bestDeltaCost := 1e308
		inserted := false
		for aIdx := 0; aIdx < dispatch.AssignsLen; aIdx++ {
			assign := &dispatch.Assigns[aIdx]
			origCost := assign.Cost
			trialOk := assign.AddShip(shipId, ori, des)
			if trialOk {
				assign.GenRoute()
				newCost := assign.Cost
				deltaCost := newCost - origCost
				if deltaCost < bestDeltaCost {
					bestDeltaCost = deltaCost
					bestAssignIdx = aIdx
				}
				assign.RemoveShip(shipId)
				assign.GenRoute()
			}
		}
		if bestAssignIdx != -1 && bestDeltaCost < 1e307 {
			finalAssign := &dispatch.Assigns[bestAssignIdx]
			ok := finalAssign.AddShip(shipId, ori, des)
			if ok {
				finalAssign.GenRoute()
				inserted = true
			}
		}
		if !inserted {
			if dispatch.AssignsLen < MAXASSIGNS {
				nextIdx := dispatch.AssignsLen
				ok := dispatch.Assigns[nextIdx].AddShip(shipId, ori, des)
				if ok {
					dispatch.Assigns[nextIdx].GenRoute()
					dispatch.AssignsLen++
					inserted = true
				} else if nextIdx > seedAssignIdx && seedAssignIdx < MAXASSIGNS {
					okSeed := dispatch.Assigns[seedAssignIdx].AddShip(shipId, ori, des)
					if okSeed {
						dispatch.Assigns[seedAssignIdx].GenRoute()
						inserted = true
					}
				}
			}
		}
		if !inserted && seedAssignIdx < MAXASSIGNS && dispatch.AssignsLen < MAXASSIGNS {
			ok := dispatch.Assigns[dispatch.AssignsLen].AddShip(shipId, ori, des)
			if ok {
				dispatch.Assigns[dispatch.AssignsLen].GenRoute()
				dispatch.AssignsLen++
				seedAssignIdx = dispatch.AssignsLen - 1
			}
		}
	}
	dispatch.RenewnTotalCost()
	return dispatch
}