package objects

type GameObject struct {
	Users *SyncIDMap[*User]
}
