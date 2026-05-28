func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
	kBest := 5
	for jj := 0; jj < len(oris); jj++ {
		bestDelta := 1e18
		bestIdx := -1
		candidates := make([]struct{ idx int; delta float64 }, 0, kBest)
		for ii := 0; ii < dispatch.AssignsLen; ii++ {
			oldCost := dispatch.Assigns[ii].Cost
			ok := dispatch.Assigns[ii].AddShip(total_ship+jj, oris[jj], dess[jj])
			if ok {
				dispatch.Assigns[ii].GenRoute()
				newCost := dispatch.Assigns[ii].Cost
				delta := newCost - oldCost
				if delta >= 0 && delta < 1e17 {
					candidates = append(candidates, struct{ idx int; delta float64 }{ii, delta})
					dispatch.Assigns[ii].RemoveShip(total_ship + jj)
					dispatch.Assigns[ii].GenRoute()
				} else {
					dispatch.Assigns[ii].RemoveShip(total_ship + jj)
					dispatch.Assigns[ii].GenRoute()
				}
			}
		}
		sort.Slice(candidates, func(a, b int) bool { return candidates[a].delta < candidates[b].delta })
		if len(candidates) > 0 {
			topK := kBest
			if len(candidates) < topK {
				topK = len(candidates)
			}
			if topK == 1 {
				bestIdx = candidates[0].idx
				bestDelta = candidates[0].delta
			} else {
				regretSum := 0.0
				for t := 0; t < topK; t++ {
					if t == 0 {
						bestIdx = candidates[t].idx
						bestDelta = candidates[t].delta
					}
					if t == 1 {
						regretSum += candidates[t].delta - bestDelta
					}
				}
				score := bestDelta + regretSum*0.3
				for t := 0; t < topK; t++ {
					curRegret := 0.0
					if t == 0 && topK > 1 {
						curRegret = candidates[1].delta - candidates[t].delta
					} else if t > 0 && topK > 1 {
						curRegret = candidates[0].delta - candidates[t].delta
					}
					curScore := candidates[t].delta + curRegret*0.3
					if curScore < score || (curScore == score && candidates[t].delta < bestDelta) {
						score = curScore
						bestIdx = candidates[t].idx
						bestDelta = candidates[t].delta
					}
				}
			}
		}
		if bestIdx >= 0 {
			dispatch.Assigns[bestIdx].AddShip(total_ship+jj, oris[jj], dess[jj])
			dispatch.Assigns[bestIdx].GenRoute()
		} else {
			fallbackOk := false
			for ii := 0; ii < dispatch.AssignsLen; ii++ {
				ok := dispatch.Assigns[ii].AddShip(total_ship+jj, oris[jj], dess[jj])
				if ok {
					dispatch.Assigns[ii].GenRoute()
					fallbackOk = true
					break
				}
			}
			if !fallbackOk {
				if dispatch.AssignsLen < MAXASSIGNS {
					idx := dispatch.AssignsLen
					dispatch.Assigns[idx].AddShip(total_ship+jj, oris[jj], dess[jj])
					dispatch.Assigns[idx].GenRoute()
					dispatch.AssignsLen++
				} else {
					minLoad := int(^uint(0) >> 1)
					sel := -1
					for ii := 0; ii < dispatch.AssignsLen; ii++ {
						load := 0
						assign := &dispatch.Assigns[ii]
						for s := 0; s < assign.StationsLen; s++ {
							if assign.Stations[s].ReqCode > 0 {
								load++
							}
						}
						if load < minLoad {
							minLoad = load
							sel = ii
						}
					}
					if sel >= 0 {
						ok2 := dispatch.Assigns[sel].AddShip(total_ship+jj, oris[jj], dess[jj])
						if ok2 {
							dispatch.Assigns[sel].GenRoute()
						} else {
							for ii := 0; ii < dispatch.AssignsLen; ii++ {
								ok3 := dispatch.Assigns[ii].AddShip(total_ship+jj, oris[jj], dess[jj])
								if ok3 {
									dispatch.Assigns[ii].GenRoute()
									break
								}
							}
						}
					}
				}
			}
		}
	}
	dispatch.RenewnTotalCost()
	return dispatch
}