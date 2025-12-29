# Notifications System Architecture & Data Flow

## Overview

The ARIA application uses a **dual notification system** that combines:
1. **REST API Notifications** - Historical/persisted notifications fetched from a backend API
2. **PubSub Real-time Notifications** - Live notifications delivered via Google Cloud PubSub and Socket.IO

Both systems work together to provide a complete notification experience with real-time updates and historical data.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    NOTIFICATION SOURCES                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. REST API                   2. Google Cloud PubSub          │
│     (Historical)                  (Real-time)                   │
│         │                              │                        │
│         │                              │                        │
│         ▼                              ▼                        │
│  ┌─────────────┐              ┌──────────────────┐            │
│  │ Backend API │              │ PubSub Topic     │            │
│  │  Endpoint   │              │ (GCP)             │            │
│  └─────────────┘              └──────────────────┘            │
│         │                              │                        │
│         │                              │                        │
└─────────┼──────────────────────────────┼────────────────────────┘
          │                              │
          │                              │
          ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  NotificationPanel Component                            │  │
│  │  - Displays notifications                                │  │
│  │  - Handles user interactions                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ▲                                     │
│                           │                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Redux Store (notificationsSlice)                        │  │
│  │  - Centralized state management                          │  │
│  │  - Deduplication logic                                   │  │
│  │  - Read/unread tracking                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│         ▲                              ▲                         │
│         │                              │                         │
│         │                              │                         │
│  ┌──────────────┐              ┌──────────────┐               │
│  │ useNotifications│            │ useSocketRedux│               │
│  │ Hook           │            │ Hook         │               │
│  └──────────────┘              └──────────────┘               │
│         │                              │                         │
│         │                              │                         │
│  ┌──────────────┐              ┌──────────────┐               │
│  │ notificationsApi│           │ Socket.IO    │               │
│  │ Service       │             │ Client        │               │
│  └──────────────┘              └──────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
          │                              │
          │                              │
          ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVER LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Next.js API Routes                                      │  │
│  │  - /api/health                                           │  │
│  │  - /api/pubsub/status                                    │  │
│  │  - /api/socket.io (Socket.IO endpoint)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ▲                                     │
│                           │                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Socket.IO Server                                        │  │
│  │  - Manages WebSocket connections                         │  │
│  │  - Handles client authentication                         │  │
│  │  - Broadcasts notifications                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│         ▲                              ▲                         │
│         │                              │                         │
│  ┌──────────────┐              ┌──────────────┐               │
│  │ socket-handlers│           │ pubsub-      │               │
│  │               │            │ standalone   │               │
│  └──────────────┘              └──────────────┘               │
│         │                              │                         │
│         │                              │                         │
│  ┌──────────────┐              ┌──────────────┐               │
│  │ connection-  │              │ pubsub-      │               │
│  │ manager      │              │ listener     │               │
│  └──────────────┘              └──────────────┘               │
│                                 │                               │
│                                 ▼                               │
│                        ┌──────────────┐                        │
│                        │ message-     │                        │
│                        │ router       │                        │
│                        └──────────────┘                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## End-to-End Data Flow

### Flow 1: REST API Notifications (Historical Data)

**Purpose**: Load previously saved notifications when the user first opens the app.

```
1. User Opens App
   │
   ▼
2. NotificationPanel Component Mounts
   │
   ▼
3. useNotificationsInitialLoad Hook Executes
   │
   ▼
4. fetchNotifications() Called (notificationsApi.ts)
   │
   ├─► GET /api/v1/notification/recent?limit=15
   │   │
   │   ├─► Headers: Authorization: Bearer <token>
   │   │
   │   └─► Response: { success: true, notifications: [...] }
   │
   ▼
5. parseNotificationsResponse() Transforms Data
   │
   ├─► Maps API format to internal Notification format
   │   - Adds 'api-' prefix to messageId
   │   - Extracts user_id, priority, task_id, etc.
   │   - Sets source: 'api'
   │
   ▼
6. Redux Action: loadNotifications()
   │
   ├─► Stores in notificationsSlice
   │   - Sets isInitialLoadComplete = true
   │   - Sorts by timestamp (newest first)
   │   - Preserves read status if notification already exists
   │
   ▼
7. NotificationPanel Renders Notifications
   │
   └─► User sees historical notifications
```

**Key Points**:
- Runs once on initial page load
- Fetches up to 15 most recent notifications
- Uses bearer token for authentication
- Sets `isInitialLoadComplete` flag to allow PubSub messages

---

### Flow 2: PubSub Real-time Notifications

**Purpose**: Deliver live notifications as they are published to the PubSub topic.

```
1. External System Publishes to PubSub Topic
   │
   ├─► Message Structure:
   │   {
   │     "data": { "message": "...", "user_id": "abc123", ... },
   │     "attributes": { "user_id": "abc123", "routing": "user" }
   │   }
   │
   ▼
2. PubSub Subscription Receives Message
   │
   ▼
3. pubsub-listener.ts (PubSubListener Class)
   │
   ├─► Listens to Google Cloud PubSub subscription
   │   - Configurable maxMessages (default: 10)
   │   - Automatic retry with exponential backoff
   │   - Handles connection errors gracefully
   │
   ├─► Emits 'message' event with PubSub Message object
   │
   ▼
4. pubsub-standalone.ts (Message Handler)
   │
   ├─► Receives message from PubSubListener
   │
   ├─► parseMessageData() - Parses JSON from message.data
   │
   ├─► Extracts user_id from:
   │   - message.attributes.user_id
   │   - parsedMessage.data.user_id
   │
   ├─► User Filtering Logic:
   │   ├─► If no user_id → Skip message (ack & return)
   │   ├─► Check if any connected user matches user_id
   │   └─► If no matching user → Skip message (ack & return)
   │
   ├─► Creates payload:
   │   {
   │     messageId: message.id,
   │     publishTime: message.publishTime,
   │     attributes: message.attributes,
   │     data: parsedMessage.data,
   │     timestamp: new Date().toISOString(),
   │     source: 'pubsub'
   │   }
   │
   ├─► Gets routing config from message attributes
   │
   ├─► Checks Socket.IO Server Availability:
   │   ├─► If no clients connected → Queue message
   │   └─► If clients available → Route immediately
   │
   ▼
5. message-router.ts (Routing Logic)
   │
   ├─► extractUserIdFromPayload() - Gets user_id from payload
   │
   ├─► If user_id exists:
   │   ├─► Find all Socket.IO connections with matching userId
   │   ├─► Emit 'notification' event to those sockets only
   │   └─► Return routing result
   │
   ├─► If no user_id (fallback):
   │   └─► Use routing strategy (broadcast/room/user)
   │
   ▼
6. Socket.IO Server Broadcasts
   │
   ├─► io.to(socketId).emit('notification', payload)
   │   - Only sends to sockets with matching userId
   │
   ▼
7. Client Receives via Socket.IO
   │
   ├─► useSocketRedux Hook Listens for 'notification' event
   │
   ├─► handleNotification() Handler:
   │   ├─► Transforms payload to Notification format
   │   ├─► Dispatches addNotification() Redux action
   │   └─► Calls optional onNotification callback
   │
   ▼
8. Redux Store Updates
   │
   ├─► notificationsSlice.addNotification() Reducer:
   │   ├─► Checks for duplicates by messageId
   │   ├─► Adds to notifications array (unshift - newest first)
   │   ├─► Updates unreadCount
   │   └─► Sets lastNotification
   │
   ▼
9. NotificationPanel Re-renders
   │
   └─► User sees new notification in real-time
```

**Key Points**:
- Real-time delivery via WebSocket
- User-based filtering ensures only matching users receive notifications
- Queue system handles messages when no clients are connected
- Automatic deduplication in Redux store

---

## Detailed File Roles

### Client-Side Files

#### 1. `components/NotificationPanel.tsx`
**Role**: UI component that displays notifications to the user

**Responsibilities**:
- Renders notification bell icon with unread count badge
- Shows dropdown panel with list of notifications
- Handles user interactions (mark as read, dismiss, mark all read)
- Formats timestamps (e.g., "5m ago", "2h ago")
- Categorizes notifications by type (pubsub, batch, ingestion, system)
- Sorts notifications (unread first, then by timestamp)
- Calls `useNotificationsInitialLoad()` to fetch API notifications on mount

**Key Features**:
- Click outside to close
- Visual indicators for unread notifications
- Empty state when no notifications
- Responsive design

---

#### 2. `hooks/useNotifications.ts`
**Role**: React hook for fetching notifications from REST API

**Responsibilities**:
- `useNotifications()` - General hook for fetching notifications
  - Supports fetch on mount, merge mode, custom token
  - Prevents concurrent fetches
  - Only fetches when user is authenticated

- `useNotificationsInitialLoad()` - Specialized hook for initial load
  - Fetches once on mount
  - Sets `isInitialLoadComplete` flag in Redux
  - Ensures API notifications load before PubSub messages

**Key Features**:
- Prevents duplicate fetches
- Handles authentication state
- Supports both replace and merge modes

---

#### 3. `hooks/useSocketRedux.ts`
**Role**: React hook that manages Socket.IO client connection and events

**Responsibilities**:
- Creates and manages Socket.IO client instance
- Registers event listeners:
  - `connect` / `disconnect` - Connection state
  - `notification` - Receives PubSub notifications
  - `message` - Receives general messages
  - `authenticated` - Confirms authentication
  - `subscribed` / `unsubscribed` - Room subscriptions
- Transforms incoming notification payloads to Redux format
- Dispatches Redux actions for notifications and messages
- Provides helper functions:
  - `authenticate(userId, token)` - Authenticate socket connection
  - `subscribe(room)` / `unsubscribe(room)` - Room management
  - `sendMessage(data)` - Send messages to server

**Key Features**:
- Auto-connects by default
- Handles reconnection logic
- Updates Redux state for connection status

---

#### 4. `components/providers/SocketProvider.tsx`
**Role**: React provider that initializes Socket.IO and authenticates connections

**Responsibilities**:
- Wraps app with Socket.IO initialization
- Calls `/api/health` and `/api/pubsub/status` on mount to ensure server is ready
- Automatically authenticates Socket.IO connection when:
  - Socket is connected
  - User is authenticated
  - User ID is available
- Uses `useSocketRedux` hook internally

**Key Features**:
- Automatic authentication on login
- Server health checks
- Retry logic for server initialization

---

#### 5. `lib/services/notificationsApi.ts`
**Role**: Service layer for REST API notification endpoints

**Responsibilities**:
- `fetchNotifications(token?, limit)` - Fetches notifications from API
  - Validates and clamps limit (1-100)
  - Handles authentication via bearer token
  - Error handling (401, 400, 404, 500)
  - Returns empty array on non-critical errors

- `parseNotificationsResponse()` - Transforms API response
  - Maps API format to internal Notification format
  - Adds `api-` prefix to messageId
  - Extracts user_id, priority, task_id to attributes
  - Sets source: 'api'

- `getNotificationsApiEndpoint()` - Returns API endpoint URL
  - Uses `NEXT_PUBLIC_NOTIFICATIONS_API_URL` env var
  - Defaults to `/api/v1/notification/recent`

**Key Features**:
- Graceful error handling
- Token support for server-side calls
- Type-safe response parsing

---

#### 6. `lib/store/slices/notificationsSlice.ts`
**Role**: Redux slice for notification state management

**State Structure**:
```typescript
{
  notifications: Notification[],
  unreadCount: number,
  lastNotification: Notification | null,
  isInitialLoadComplete: boolean
}
```

**Reducers**:
- `addNotification` - Adds new notification (from PubSub or API)
  - Checks for duplicates by messageId
  - Handles API notifications (api-* prefix)
  - Increments unreadCount
  - Adds to beginning of array (newest first)

- `loadNotifications` - Replaces all notifications (initial API load)
  - Preserves read status for existing notifications
  - Sorts by timestamp
  - Sets isInitialLoadComplete = true

- `mergeNotifications` - Merges API notifications with existing
  - Avoids duplicates
  - Only adds new notifications

- `markNotificationAsRead` - Marks single notification as read
- `markAllNotificationsAsRead` - Marks all as read
- `removeNotification` - Removes notification from list
- `clearNotifications` - Clears all notifications
- `setInitialLoadComplete` - Sets initial load flag

**Key Features**:
- Automatic deduplication
- Read/unread tracking
- Timestamp-based sorting
- Handles both API and PubSub sources

---

### Server-Side Files

#### 7. `lib/server/startup.ts`
**Role**: Server initialization module

**Responsibilities**:
- Auto-initializes PubSub listener on server startup
- Calls `initializeStandalonePubSub()` when module loads
- Ensures PubSub starts listening as soon as server is ready
- Prevents duplicate initialization

**Key Features**:
- Runs only on server-side (checks `typeof window === 'undefined'`)
- One-time initialization with promise caching

---

#### 8. `lib/server/pubsub-config/pubsub-config.ts`
**Role**: Configuration for Google Cloud PubSub

**Responsibilities**:
- Provides PubSub configuration from environment variables
- Returns:
  - `projectId` - GCP project ID
  - `subscriptionName` - PubSub subscription name
  - `topicName` - PubSub topic name

**Environment Variables**:
- `GCP_PROJECT_ID` (default: 'gabeo-poc')
- `PUBSUB_SUBSCRIPTION` (default: full subscription path)
- `PUBSUB_TOPIC` (default: full topic path)

---

#### 9. `lib/server/pubsub-listener.ts`
**Role**: Low-level PubSub subscription manager

**Class: PubSubListener**

**Responsibilities**:
- Manages Google Cloud PubSub subscription connection
- Handles authentication via `GOOGLE_APPLICATION_CREDENTIALS`
- Listens for messages from PubSub subscription
- Implements retry logic with exponential backoff
- Verifies subscription exists before starting
- Manages message flow control (maxMessages)

**Key Methods**:
- `constructor(config)` - Initializes PubSub client
- `onMessage(handler)` - Registers message handler
- `onError(handler)` - Registers error handler
- `start()` - Starts listening to subscription
- `stop()` - Stops listening and cleans up
- `isActive()` - Checks if listener is active
- `getSubscriptionInfo()` - Returns subscription metadata

**Key Features**:
- Automatic retry on connection failures
- Subscription verification with timeout
- Flow control to limit concurrent messages
- Graceful error handling

---

#### 10. `lib/server/pubsub-standalone.ts`
**Role**: High-level PubSub message processor and queue manager

**Responsibilities**:
- Initializes and manages PubSubListener instance
- Processes incoming PubSub messages
- Implements message queue for when no clients are connected
- Filters messages by user_id
- Routes messages to Socket.IO clients
- Tracks message statistics (received, acked, nacked, queued, dropped, broadcasted)

**Key Functions**:
- `initializeStandalonePubSub()` - Sets up PubSub listener
- `processMessageQueue()` - Processes queued messages when clients connect
- `startQueueProcessing()` - Starts periodic queue processing
- `stopQueueProcessing()` - Stops queue processing
- `setGlobalIOServerForPubSub(io)` - Registers Socket.IO server
- `getStandalonePubSubStatus()` - Returns status and statistics

**Message Processing Flow**:
1. Receives message from PubSubListener
2. Parses message data (JSON)
3. Extracts user_id from attributes or data
4. **Filters**: Skips if no user_id or no matching connected user
5. Creates payload object
6. Gets routing configuration
7. Checks if Socket.IO server is available
8. If clients connected → Routes immediately
9. If no clients → Queues message (max 100, max age 30s)
10. Acknowledges or nacks message based on result

**Queue Management**:
- Max queue size: 100 messages
- Max queue age: 30 seconds (stale messages are nacked)
- Processes queue when clients connect
- Drops messages if queue is full

**Key Features**:
- User-based filtering
- Message queuing for offline clients
- Automatic stale message cleanup
- Comprehensive statistics tracking

---

#### 11. `lib/server/pubsub/helpers/message-parser.ts`
**Role**: Parses PubSub message data

**Function: `parseMessageData(message)`**

**Responsibilities**:
- Converts PubSub message.data (Buffer) to string
- Attempts JSON parsing
- Returns structured object:
  ```typescript
  {
    data: any,        // Parsed JSON or { text: string }
    isJson: boolean,  // Whether parsing succeeded
    rawData: string  // Original string
  }
  ```

**Key Features**:
- Handles both JSON and plain text messages
- Graceful fallback for non-JSON data

---

#### 12. `lib/server/pubsub/helpers/message-router.ts`
**Role**: Routes messages to specific Socket.IO clients based on user_id

**Key Functions**:
- `routeMessage(io, payload, config, connections)` - Main routing function
  - **Primary Logic**: If payload has user_id, only send to matching users
  - Falls back to routing strategy if no user_id
  - Returns routing result (clients notified, strategy, target)

- `extractUserIdFromPayload(payload)` - Extracts user_id
  - Checks: payload.attributes.user_id, payload.data.user_id
  - Also checks for userId (camelCase) variants

- `getRoutingConfig(message)` - Gets routing config from PubSub message
  - Extracts routing strategy (broadcast/room/user)
  - Extracts targetRoom and targetUserId from attributes

- `routeToUser()` - Routes to specific user's sockets
- `routeToRoom()` - Routes to Socket.IO room
- `routeBroadcast()` - Broadcasts to all clients (with user_id filtering)

**User Filtering Logic**:
```typescript
if (messageUserId) {
  // Find all sockets for this user
  const userSockets = connections
    .filter(conn => conn.userId === messageUserId)
    .map(conn => conn.socketId);
  
  // Send only to those sockets
  userSockets.forEach(socketId => {
    io.to(socketId).emit('notification', payload);
  });
}
```

**Key Features**:
- User-based filtering is primary mechanism
- Supports fallback routing strategies
- Returns detailed routing results

---

#### 13. `lib/server/socket-handlers.ts`
**Role**: Socket.IO event handlers for client connections

**Function: `setupSocketHandlers(socket)`**

**Event Handlers**:
- `connect` - Client connects
  - Adds connection to connection manager
  - Triggers queued message processing
  - Emits 'connected' event

- `authenticate` - Client authenticates
  - Receives: `{ userId, token }`
  - Updates userId in connection manager
  - Emits 'authenticated' confirmation

- `heartbeat` - Client heartbeat
  - Updates lastHeartbeat timestamp
  - Emits 'heartbeat-ack'

- `subscribe` / `unsubscribe` - Room management
  - Joins/leaves Socket.IO rooms
  - Emits confirmation

- `message` - Client sends message
  - Broadcasts to all other clients
  - Emits 'message-sent' confirmation

- `disconnect` - Client disconnects
  - Removes from connection manager

**Key Features**:
- Manages connection lifecycle
- Handles user authentication
- Processes queued messages on new connections

---

#### 14. `lib/server/connection-manager.ts`
**Role**: Tracks Socket.IO client connections and user associations

**Data Structure**:
```typescript
Map<socketId, ConnectionInfo>
ConnectionInfo {
  socketId: string,
  userId?: string,
  connectedAt: Date,
  lastHeartbeat: Date
}
```

**Functions**:
- `addConnection(socketId, userId?)` - Adds new connection
- `removeConnection(socketId)` - Removes connection
- `updateUserId(socketId, userId)` - Updates user ID for connection
- `updateHeartbeat(socketId)` - Updates heartbeat timestamp
- `getAllConnections()` - Returns all connections
- `getConnectionCount()` - Returns connection count
- `clearAllConnections()` - Clears all connections

**Key Features**:
- In-memory storage (Map)
- Tracks user associations for filtering
- Heartbeat tracking for connection health

---

## User Authentication Flow

```
1. User Logs In
   │
   ▼
2. Auth State Updated (Redux)
   │
   ├─► user.uid available
   ├─► token available
   └─► isAuthenticated = true
   │
   ▼
3. SocketProvider Detects Auth State
   │
   ├─► useEffect triggers when:
   │   - isConnected = true
   │   - isAuthenticated = true
   │   - user.uid exists
   │
   ▼
4. Calls authenticate(user.uid, token)
   │
   ├─► useSocketRedux.authenticate()
   │   └─► socket.emit('authenticate', { userId: user.uid, token })
   │
   ▼
5. Server Receives 'authenticate' Event
   │
   ├─► socket-handlers.ts
   │   └─► updateUserId(socket.id, data.userId)
   │
   ▼
6. Connection Manager Updates
   │
   ├─► connection-manager.ts
   │   └─► connections.set(socketId, { ..., userId: user.uid })
   │
   ▼
7. User ID Now Available for Message Filtering
   │
   └─► PubSub messages with matching user_id will be delivered
```

---

## Message Deduplication

The system prevents duplicate notifications through multiple mechanisms:

1. **Redux Store Deduplication** (`notificationsSlice.ts`):
   - Checks `messageId` before adding
   - Handles API notifications (api-* prefix) specially
   - Prevents same notification from appearing twice

2. **PubSub Message Acknowledgment**:
   - Messages are acked only after successful delivery
   - Prevents PubSub from redelivering processed messages

3. **Message Queue Deduplication**:
   - Queue checks for existing messages before adding
   - Prevents queue overflow from duplicates

---

## Error Handling & Resilience

### PubSub Connection Failures
- Automatic retry with exponential backoff
- Max 10 retry attempts
- Graceful degradation (logs errors, continues)

### Socket.IO Connection Failures
- Automatic reconnection (up to 10 attempts)
- Reconnection delay: 1-5 seconds
- Connection state tracked in Redux

### API Failures
- Returns empty array on non-critical errors
- 401 errors throw (triggers auth flow)
- 500 errors throw (service unavailable)
- 404 errors return empty (service might not be available)

### Message Processing Failures
- Failed messages are nacked (redelivered by PubSub)
- Queue prevents message loss when clients disconnect
- Stale messages (30s+) are nacked to allow redelivery

---

## Performance Optimizations

1. **Message Queue**: Prevents message loss when clients disconnect
2. **Connection Tracking**: Efficient Map-based storage
3. **Redux Deduplication**: Prevents duplicate renders
4. **Lazy Loading**: API notifications load only when needed
5. **Batch Processing**: Queue processes multiple messages at once
6. **Flow Control**: PubSub limits concurrent messages (maxMessages: 10)

---

## Security Considerations

1. **User-Based Filtering**: Only matching users receive notifications
2. **Bearer Token Authentication**: API calls require valid token
3. **Socket Authentication**: User ID must be authenticated before receiving messages
4. **Connection Validation**: Server validates user associations

---

## Configuration

### Environment Variables

**Client-Side**:
- `NEXT_PUBLIC_NOTIFICATIONS_API_URL` - API endpoint URL
- `NEXT_PUBLIC_SOCKET_IO_PATH` - Socket.IO path (default: '/api/socket.io')

**Server-Side**:
- `GCP_PROJECT_ID` - Google Cloud Project ID
- `PUBSUB_SUBSCRIPTION` - PubSub subscription name
- `PUBSUB_TOPIC` - PubSub topic name
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to GCP credentials JSON

---

## Summary

The notifications system provides:
- ✅ **Historical Data**: REST API loads saved notifications
- ✅ **Real-time Updates**: PubSub delivers live notifications
- ✅ **User Filtering**: Only matching users receive notifications
- ✅ **Resilience**: Queue system, retry logic, error handling
- ✅ **Deduplication**: Prevents duplicate notifications
- ✅ **Performance**: Efficient state management and routing

Both systems work together seamlessly, with API notifications providing context and PubSub notifications delivering real-time updates.

