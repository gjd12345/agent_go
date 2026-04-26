func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
	if len(oris) <= 5 {
		const topK = 2
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
			inserted := false
			for pos := 0; pos < topLen; pos++ {
				ii := topIdx[pos]
				if !dispatch.Assigns[ii].AddShip(total_ship+jj, oris[jj], dess[jj]) {
					continue
				}
				dispatch.Assigns[ii].GenRoute()
				if dispatch.Assigns[ii].Cost >= 0 {
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

	if len(oris) <= 10 {
		const topK = 3
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
					score := (newCost - oldCost) + 0.03*topDist[pos]
					if score < bestScore {
						bestScore = score
						bestIdx = ii
					}
				}
				dispatch.Assigns[ii].RemoveShip(total_ship + jj)
				dispatch.Assigns[ii].GenRoute()
			}
			if bestIdx >= 0 {
				dispatch.Assigns[bestIdx].AddShip(total_ship+jj, oris[jj], dess[jj])
				dispatch.Assigns[bestIdx].GenRoute()
			} else if dispatch.AssignsLen < MAXASSIGNS {
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

	var order [MAXASSIGNS]int
	randLimit := 0
	for ii := range order {
		order[ii] = ii
		if ii < dispatch.AssignsLen && dispatch.Assigns[ii].StationsLen > 0 {
			order[ii], order[randLimit] = order[randLimit], ii
			randLimit++
		}
	}
	rand.Shuffle(randLimit, func(i, j int) {
		order[i], order[j] = order[j], order[i]
	})
	for jj := range oris {
		for _, ii := range order {
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
				break
			}
			dispatch.Assigns[ii].RemoveShip(total_ship + jj)
			dispatch.Assigns[ii].GenRoute()
		}
	}
	dispatch.RenewnTotalCost()
	return dispatch
}
