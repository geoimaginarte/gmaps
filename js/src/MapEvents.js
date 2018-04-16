
// Events that need to be broadcast across the application,
// rather than just communication between the view and its model

export const mapEventTypes = {
    MAP_DOWNLOAD_ERROR: 'MAP_DOWNLOAD_ERROR'
}

export class MapEvents {
    static downloadError(errorMessage) {
        return { errorMessage }
    }
}
