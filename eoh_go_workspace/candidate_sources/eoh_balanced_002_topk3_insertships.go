func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
	const topK = 3
	const pickupWeight = 0.1

	var fallbackOrder [MAXASSIGNS]int
	for ii := range fallbackOrder {
		fallbackOrder[ii] = ii
	}

	for jj := range oris {
		var topIdx [topK]int
		var topDist [topK]float64
		topLen := 0

		for ii := 0; ii < dispatch.AssignsLen; ii++ {
			if dispatch.Assigns[ii].StationsLen <= 0 {
				continue
			}
			dist := cal_dis(dispatch.Assigns[ii].StationCurrent, oris[jj])
			pos := topLen
			if pos >= topK {
				pos = topK - 1
				if dist >= topDist[pos] {
					continue
				}
			} else {
				topLen++
			}
			for pos > 0 && dist < topDist[pos-1] {
				topIdx[pos] = topIdx[pos-1]
				topDist[pos] = topDist[pos-1]
				pos--
			}
			topIdx[pos] = ii
			topDist[pos] = dist
		}

		bestIdx := -1
		bestScore := 1e18
		for pos := 0; pos < topLen; pos++ {
			ii := topIdx[pos]
			oldCost := dispatch.Assigns[ii].Cost
			if !dispatch.Assigns[ii].AddShip(total_ship+jj, oris[jj], dess[jj]) {
				continue
			}
			dispatch.Assigns[ii].GenRoute()
			newCost := dispatch.Assigns[ii].Cost
			if newCost >= 0 {
				score := (newCost - oldCost) + pickupWeight*topDist[pos]
				if score < bestScore {
					bestScore = score
					bestIdx = ii
				}
			}
			dispatch.Assigns[ii].RemoveShip(total_ship + jj)
			dispatch.Assigns[ii].GenRoute()
		}

		if dispatch.AssignsLen < MAXASSIGNS {
			ii := dispatch.AssignsLen
			oldCost := dispatch.Assigns[ii].Cost
			dist := cal_dis(dispatch.Assigns[ii].StationCurrent, oris[jj])
			if dispatch.Assigns[ii].AddShip(total_ship+jj, oris[jj], dess[jj]) {
				dispatch.Assigns[ii].GenRoute()
				newCost := dispatch.Assigns[ii].Cost
				if newCost >= 0 {
					score := (newCost - oldCost) + pickupWeight*dist
					if score < bestScore {
						bestScore = score
						bestIdx = ii
					}
				}
				dispatch.Assigns[ii].RemoveShip(total_ship + jj)
				dispatch.Assigns[ii].GenRoute()
			}
		}

		if bestIdx >= 0 {
			if dispatch.Assigns[bestIdx].AddShip(total_ship+jj, oris[jj], dess[jj]) {
				dispatch.Assigns[bestIdx].GenRoute()
				if dispatch.Assigns[bestIdx].Cost >= 0 {
					if bestIdx >= dispatch.AssignsLen {
						dispatch.AssignsLen = bestIdx + 1
					}
					continue
				}
				dispatch.Assigns[bestIdx].RemoveShip(total_ship + jj)
				dispatch.Assigns[bestIdx].GenRoute()
			}
		}

		randLimit := 0
		for ii := range fallbackOrder {
			fallbackOrder[ii] = ii
			if ii < dispatch.AssignsLen && dispatch.Assigns[ii].StationsLen > 0 {
				fallbackOrder[ii], fallbackOrder[randLimit] = fallbackOrder[randLimit], ii
				randLimit++
			}
		}
		rand.Shuffle(randLimit, func(i, j int) {
			fallbackOrder[i], fallbackOrder[j] = fallbackOrder[j], fallbackOrder[i]
		})

		inserted := false
		for _, ii := range fallbackOrder {
			if ii > dispatch.AssignsLen || ii >= MAXASSIGNS {
				continue
			}
			if !dispatch.Assigns[ii].AddShip(total_ship+jj, oris[jj], dess[jj]) {
				continue
			}
			dispatch.Assigns[ii].GenRoute()
			if dispatch.Assigns[ii].Cost >= 0 {
				if ii >= dispatch.AssignsLen {
					dispatch.AssignsLen = ii + 1
				}
				inserted = true
				break
			}
			dispatch.Assigns[ii].RemoveShip(total_ship + jj)
			dispatch.Assigns[ii].GenRoute()
		}
		if !inserted && dispatch.AssignsLen < MAXASSIGNS {
			ii := dispatch.AssignsLen
			if dispatch.Assigns[ii].AddShip(total_ship+jj, oris[jj], dess[jj]) {
				dispatch.Assigns[ii].GenRoute()
				if dispatch.Assigns[ii].Cost >= 0 {
					dispatch.AssignsLen = ii + 1
				}
			}
		}
	}
	dispatch.RenewnTotalCost()
	return dispatch
}
