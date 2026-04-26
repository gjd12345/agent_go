func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
	tightWindow := false
	for jj := range oris {
		if oris[jj].TimeEnd-oris[jj].TimeStart < 0 || dess[jj].TimeEnd-dess[jj].TimeStart < 0 {
			tightWindow = true
			break
		}
	}

	if len(oris) <= 5 && !tightWindow {
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

	if len(oris) <= 10 && !tightWindow {
		var rand_range [MAXASSIGNS]int
		var rand_limit int = 0
		for ii := range rand_range {
			rand_range[ii] = ii
			if ii < dispatch.AssignsLen && dispatch.Assigns[ii].StationsLen > 0 {
				rand_range[ii], rand_range[rand_limit] = rand_range[rand_limit], ii
				rand_limit += 1
			}
		}
		rand.Shuffle(rand_limit, func(i, j int) {
			rand_range[i], rand_range[j] = rand_range[j], rand_range[i]
		})
		for jj := range oris {
			bestIdx := -1
			bestCost := 1e18
			for _, ii := range rand_range {
				if ii >= dispatch.AssignsLen && dispatch.Assigns[dispatch.AssignsLen].StationsLen > 0 {
					continue
				}
				if !dispatch.Assigns[ii].AddShip(total_ship+jj, oris[jj], dess[jj]) {
					dispatch.Assigns[ii].RemoveShip(total_ship + jj)
					continue
				}
				oldCost := dispatch.Assigns[ii].Cost
				dispatch.Assigns[ii].GenRoute()
				newCost := dispatch.Assigns[ii].Cost
				if newCost >= 0 && (newCost-oldCost) < bestCost {
					bestCost = newCost - oldCost
					bestIdx = ii
				}
				dispatch.Assigns[ii].RemoveShip(total_ship + jj)
				dispatch.Assigns[ii].GenRoute()
			}
			if bestIdx == -1 {
				bestIdx = dispatch.AssignsLen
			}
			dispatch.Assigns[bestIdx].AddShip(total_ship+jj, oris[jj], dess[jj])
			dispatch.Assigns[bestIdx].GenRoute()
			if bestIdx >= dispatch.AssignsLen {
				dispatch.AssignsLen += 1
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
		inserted := false
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
