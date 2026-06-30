func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
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
			if ii < dispatch.AssignsLen && dispatch.Assigns[ii].StationsLen <= 0 {
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
