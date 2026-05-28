func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
	const (
		slackWeight    = 0.6
		costWeight     = 0.4
		normalizeBase  = 50000.0
		improveFactor  = 1.08
		minSlackThresh = 3600
	)
	for jj := range oris {
		ori, des := oris[jj], dess[jj]
		shipID := total_ship + jj
		bestScore := 1e300
		bestIdx := -1
		var bestDelta float64
		var feasibleFound bool
		for ii := 0; ii < dispatch.AssignsLen; ii++ {
			prevCost := dispatch.Assigns[ii].Cost
			if prevCost < 0 {
				continue
			}
			ok := dispatch.Assigns[ii].AddShip(shipID, ori, des)
			if !ok {
				continue
			}
			dispatch.Assigns[ii].GenRoute()
			newCost := dispatch.Assigns[ii].Cost
			if newCost < 0 {
				dispatch.Assigns[ii].RemoveShip(shipID)
				dispatch.Assigns[ii].GenRoute()
				continue
			}
			feasibleFound = true
			delta := newCost - prevCost
			normDelta := delta / normalizeBase
			timeSlack := float64(des.TimeEnd - des.TimeStart)
			if timeSlack < minSlackThresh {
				timeSlack = minSlackThresh
			}
			score := costWeight*normDelta + slackWeight*(normalizeBase/timeSlack)
			if score < bestScore {
				bestScore = score
				bestIdx = ii
				bestDelta = delta
			}
			dispatch.Assigns[ii].RemoveShip(shipID)
			dispatch.Assigns[ii].GenRoute()
		}
		if !feasibleFound && bestIdx < 0 {
			for ii := 0; ii < dispatch.AssignsLen; ii++ {
				prevCost := dispatch.Assigns[ii].Cost
				if prevCost < 0 {
					continue
				}
				ok := dispatch.Assigns[ii].AddShip(shipID, ori, des)
				if ok {
					dispatch.Assigns[ii].GenRoute()
					newCost := dispatch.Assigns[ii].Cost
					if newCost >= 0 {
						bestIdx = ii
						bestDelta = newCost - prevCost
						dispatch.Assigns[ii].RemoveShip(shipID)
						dispatch.Assigns[ii].GenRoute()
						break
					}
					dispatch.Assigns[ii].RemoveShip(shipID)
					dispatch.Assigns[ii].GenRoute()
				}
			}
		}
		selectedIdx := bestIdx
		if selectedIdx >= 0 && feasibleFound {
			for ii := 0; ii < dispatch.AssignsLen; ii++ {
				if ii == bestIdx {
					continue
				}
				prevCost := dispatch.Assigns[ii].Cost
				if prevCost < 0 {
					continue
				}
				ok := dispatch.Assigns[ii].AddShip(shipID, ori, des)
				if !ok {
					continue
				}
				dispatch.Assigns[ii].GenRoute()
				newCost := dispatch.Assigns[ii].Cost
				if newCost < 0 {
					dispatch.Assigns[ii].RemoveShip(shipID)
					dispatch.Assigns[ii].GenRoute()
					continue
				}
				delta := newCost - prevCost
				if delta < bestDelta*improveFactor {
					selectedIdx = ii
					bestDelta = delta
				}
				dispatch.Assigns[ii].RemoveShip(shipID)
				dispatch.Assigns[ii].GenRoute()
				if selectedIdx != bestIdx {
					break
				}
			}
		}
		if selectedIdx < 0 {
			seedIdx := dispatch.AssignsLen
			if seedIdx < MAXASSIGNS {
				ok := dispatch.Assigns[seedIdx].AddShip(shipID, ori, des)
				if ok {
					dispatch.Assigns[seedIdx].GenRoute()
					if dispatch.Assigns[seedIdx].Cost >= 0 {
						dispatch.AssignsLen++
						selectedIdx = seedIdx
					} else {
						dispatch.Assigns[seedIdx].RemoveShip(shipID)
						dispatch.Assigns[seedIdx].GenRoute()
					}
				}
			}
		}
		if selectedIdx < 0 {
			for ii := 0; ii < MAXASSIGNS; ii++ {
				ok := dispatch.Assigns[ii].AddShip(shipID, ori, des)
				if ok {
					dispatch.Assigns[ii].GenRoute()
					if dispatch.Assigns[ii].Cost >= 0 {
						if ii >= dispatch.AssignsLen {
							dispatch.AssignsLen = ii + 1
						}
						selectedIdx = ii
						break
					}
					dispatch.Assigns[ii].RemoveShip(shipID)
					dispatch.Assigns[ii].GenRoute()
				}
			}
		}
		if selectedIdx >= 0 {
			dispatch.Assigns[selectedIdx].AddShip(shipID, ori, des)
			dispatch.Assigns[selectedIdx].GenRoute()
		}
	}
	dispatch.RenewnTotalCost()
	return dispatch
}