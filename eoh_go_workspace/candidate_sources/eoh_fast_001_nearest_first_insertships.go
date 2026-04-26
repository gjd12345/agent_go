func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
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
					inserted = true
				} else {
					dispatch.Assigns[ii].RemoveShip(total_ship + jj)
					dispatch.Assigns[ii].GenRoute()
				}
			}
		}

		if !inserted {
			for ii := 0; ii <= dispatch.AssignsLen && ii < MAXASSIGNS; ii++ {
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
	}
	dispatch.RenewnTotalCost()
	return dispatch
}
