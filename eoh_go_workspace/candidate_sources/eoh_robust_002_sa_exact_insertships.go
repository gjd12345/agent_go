func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
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
		for _, ii := range rand_range {
			if !dispatch.Assigns[ii].AddShip(total_ship+jj, oris[jj], dess[jj]) {
				dispatch.Assigns[ii].Cost = -1
			} else {
				dispatch.Assigns[ii].GenRoute()
			}
			if dispatch.Assigns[ii].Cost < 0 {
				dispatch.Assigns[ii].RemoveShip(total_ship + jj)
				dispatch.Assigns[ii].GenRoute()
			} else {
				if ii >= dispatch.AssignsLen {
					dispatch.AssignsLen += 1
				}
				break
			}
			if ii >= dispatch.AssignsLen {
				break
			}
		}
	}
	dispatch.RenewnTotalCost()
	return dispatch
}
