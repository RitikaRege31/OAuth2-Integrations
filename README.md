# Notifications Flow - Error Handling and Edge Cases Documentation

## Overview

This document provides a comprehensive overview of all error types and edge cases carefully handled throughout the notifications flow, including WebSocket connections, PubSub message processing, API interactions, and state management.

---

## 1. WebSocket Connection Errors

### 1.1 Connection Failures

**Error Type**: `SOCKET_CONNECTION_FAILED`

**Handled Scenarios**:
- Initial connection attempt fails due to network issues
- Server is unavailable or unreachable
- Connection timeout during handshake (20 seconds)
- DNS resolution failures
- Firewall or proxy blocking WebSocket connections

**Recovery Strategy**: Automatic retry with exponential backoff
- Reconnection attempts: Up to 10 attempts
- Initial delay: 1 second
- Maximum delay: 5 seconds between attempts
- Recovery action: RETRY

**Edge Cases**:
- Connection fails immediately after page load
- Connection drops during active session
- Multiple rapid connection attempts prevented by connection state checks

### 1.2 Disconnection Events

**Error Type**: `SOCKET_DISCONNECTED`

**Handled Scenarios**:
- Unexpected disconnection from server
- Network interruption (WiFi drop, mobile network switch)
- Server-side connection termination
- Client-side navigation causing connection loss

**Recovery Strategy**: Automatic reconnection with state preservation
- Heartbeat mechanism stops immediately
- Connection state updated in Redux store
- Automatic reconnection initiated
- Recovery action: RETRY

**Edge Cases**:
- Disconnection during message transmission
- Multiple disconnection events in rapid succession
- Disconnection while processing queued notifications

### 1.3 Reconnection Failures

**Error Type**: `SOCKET_RECONNECT_FAILED`

**Handled Scenarios**:
- All reconnection attempts exhausted (10 attempts)
- Persistent network issues preventing reconnection
- Server permanently unavailable
- Authentication failures during reconnection

**Recovery Strategy**: 
- Maximum retry attempts: 10
- Recovery action: RETRY
- Error logged with severity: HIGH
- User notified of connection issues

**Edge Cases**:
- Intermittent connectivity causing repeated failures
- Reconnection succeeds but immediately fails again
- Partial reconnection (connected but not authenticated)

### 1.4 Emit Failures

**Error Type**: `SOCKET_EMIT_FAILED`

**Handled Scenarios**:
- Attempting to emit message when socket is disconnected
- Message payload too large
- Socket.IO internal errors during emission
- Network issues during message transmission

**Recovery Strategy**: Message queuing for later transmission
- Recovery action: QUEUE
- Messages stored for retry when connection restored
- Error severity: MEDIUM

**Edge Cases**:
- Emit fails for critical messages (notifications)
- Multiple emit failures in sequence
- Emit succeeds but message not received by server

### 1.5 User Not Found

**Error Type**: `SOCKET_USER_NOT_FOUND`

**Handled Scenarios**:
- Routing notification to user ID that has no active connections
- User logged out but notification still being routed
- Invalid or non-existent user ID in message

**Recovery Strategy**: Skip message processing
- Recovery action: SKIP
- Error severity: LOW
- Message acknowledged to prevent redelivery

**Edge Cases**:
- User disconnects between message receipt and routing
- Multiple notifications for same non-existent user
- User ID format mismatch

---

## 2. PubSub Connection and Subscription Errors

### 2.1 PubSub Connection Failures

**Error Type**: `PUBSUB_CONNECTION_FAILED`

**Handled Scenarios**:
- Google Cloud PubSub service unavailable
- Network connectivity issues to GCP
- Authentication/authorization failures
- PubSub client initialization errors
- Subscription listener startup failures

**Recovery Strategy**: Retry with exponential backoff
- Maximum retry attempts: 10
- Recovery action: RETRY
- Error severity: CRITICAL
- Automatic retry scheduling enabled

**Edge Cases**:
- Connection fails during application startup
- Intermittent GCP service outages
- Credential expiration during runtime
- Rate limiting from GCP

### 2.2 Missing Subscription

**Error Type**: `PUBSUB_SUBSCRIPTION_MISSING`

**Handled Scenarios**:
- Subscription does not exist in Google Cloud Console
- Subscription deleted or renamed
- Incorrect subscription name in configuration
- Subscription not accessible due to permissions

**Recovery Strategy**: Abort operation (non-recoverable)
- Recovery action: ABORT
- Error severity: CRITICAL
- Application cannot proceed without subscription
- Clear error message provided for configuration fix

**Edge Cases**:
- Subscription exists but not accessible
- Subscription name typo in environment variables
- Subscription in different project/region

---

## 3. PubSub Message Processing Errors

### 3.1 Message Parse Failures

**Error Type**: `PUBSUB_MESSAGE_PARSE_FAILED`

**Handled Scenarios**:
- Invalid JSON format in message payload
- Malformed message structure
- Encoding issues (non-UTF-8 content)
- Corrupted message data
- Missing required fields in message

**Recovery Strategy**: Skip malformed message
- Recovery action: SKIP
- Error severity: MEDIUM
- Message nacked to prevent reprocessing
- Error logged with message ID for debugging

**Edge Cases**:
- Partial JSON causing parse errors
- Messages with unexpected data types
- Empty or null message payloads
- Messages exceeding size limits

### 3.2 Missing User ID

**Error Type**: `PUBSUB_MESSAGE_MISSING_USER_ID`

**Handled Scenarios**:
- Message attributes missing user_id field
- Message data missing user identifier
- User ID in unexpected location (nested objects)
- Multiple user ID fields with none matching expected format

**Recovery Strategy**: Skip message (cannot route without user)
- Recovery action: SKIP
- Error severity: LOW
- Message acknowledged to prevent redelivery
- Multiple user ID field locations checked before skipping

**Edge Cases**:
- User ID present but in wrong format
- User ID in nested attributes object
- Multiple potential user ID fields with conflicts

### 3.3 Routing Failures

**Error Type**: `PUBSUB_MESSAGE_ROUTING_FAILED`

**Handled Scenarios**:
- Unable to determine routing strategy
- Target room does not exist
- Target user has no active connections
- Socket.IO emit fails during routing
- Connection manager errors

**Recovery Strategy**: Queue message for later processing
- Recovery action: QUEUE
- Error severity: MEDIUM
- Message queued with timestamp
- Retry when connections available

**Edge Cases**:
- Routing succeeds but message not delivered
- Partial routing (some sockets receive, others don't)
- Routing configuration conflicts

### 3.4 Message Queue Overflow

**Error Type**: `PUBSUB_MESSAGE_QUEUE_OVERFLOW`

**Handled Scenarios**:
- Message queue exceeds maximum capacity
- Too many messages queued due to connection issues
- Queue processing slower than message arrival rate
- Backlog of messages waiting for connection

**Recovery Strategy**: Skip oldest messages
- Recovery action: SKIP
- Error severity: HIGH
- Oldest messages removed from queue
- Prevents memory exhaustion

**Edge Cases**:
- Queue fills up rapidly during connection outage
- Queue processing stops but messages keep arriving
- Queue size limits reached during high traffic

### 3.5 Stale Messages

**Error Type**: `PUBSUB_MESSAGE_STALE`

**Handled Scenarios**:
- Messages queued longer than maximum age threshold
- Messages older than acceptable processing window
- Time-sensitive messages that are no longer relevant

**Recovery Strategy**: Nack and remove stale messages
- Recovery action: SKIP
- Error severity: MEDIUM
- Stale messages identified and nacked
- Prevents processing outdated information

**Edge Cases**:
- Messages become stale during queue processing
- Stale message detection during high load
- Messages with time-sensitive data

### 3.6 Acknowledgment Failures

**Error Type**: `PUBSUB_MESSAGE_ACK_FAILED`

**Handled Scenarios**:
- Failed to acknowledge successfully processed message
- PubSub service unavailable during ack
- Network issues during acknowledgment
- Message already acknowledged or expired

**Recovery Strategy**: Retry acknowledgment
- Recovery action: RETRY
- Error severity: MEDIUM
- Maximum retries: 3
- Prevents message redelivery

**Edge Cases**:
- Ack fails after successful processing
- Multiple ack attempts for same message
- Ack timeout issues

### 3.7 Negative Acknowledgment Failures

**Error Type**: `PUBSUB_MESSAGE_NACK_FAILED`

**Handled Scenarios**:
- Failed to nack message that should be redelivered
- PubSub service unavailable during nack
- Network issues during negative acknowledgment
- Message already processed or expired

**Recovery Strategy**: Retry nack operation
- Recovery action: RETRY
- Error severity: MEDIUM
- Maximum retries: 3
- Ensures message redelivery when appropriate

**Edge Cases**:
- Nack fails for stale messages
- Nack fails during error handling
- Multiple nack attempts for same message

---

## 4. API and Service Errors

### 4.1 API Fetch Failures

**Error Type**: `API_FETCH_FAILED`

**Handled Scenarios**:
- HTTP request to notifications API fails
- Network timeout during API call
- CORS errors preventing API access
- Invalid API endpoint configuration
- Request payload errors

**Recovery Strategy**: Retry with backoff
- Recovery action: RETRY
- Error severity: MEDIUM
- Maximum retries: 3
- Prevents concurrent fetch attempts

**Edge Cases**:
- API fails during initial load
- Partial API response (connection drops mid-request)
- API returns error status codes

### 4.2 Authentication Required

**Error Type**: `API_AUTH_REQUIRED`

**Handled Scenarios**:
- Missing or invalid authentication token
- Token expired during API call
- Unauthorized access to notifications endpoint
- Session expired

**Recovery Strategy**: Abort and require re-authentication
- Recovery action: ABORT
- Error severity: HIGH
- User must re-authenticate
- Prevents unauthorized data access

**Edge Cases**:
- Token expires during long-running request
- Invalid token format
- Token missing from request headers

### 4.3 Service Unavailable

**Error Type**: `API_SERVICE_UNAVAILABLE`

**Handled Scenarios**:
- Backend API service down or unreachable
- 503 Service Unavailable HTTP status
- API rate limiting exceeded
- Maintenance mode on backend

**Recovery Strategy**: Retry with exponential backoff
- Recovery action: RETRY
- Error severity: HIGH
- Maximum retries: 5
- Longer delays between retries

**Edge Cases**:
- Service becomes unavailable during request
- Intermittent service availability
- Service overload causing timeouts

### 4.4 Invalid API Response

**Error Type**: `API_INVALID_RESPONSE`

**Handled Scenarios**:
- API returns unexpected response format
- Missing required fields in response
- Invalid JSON in response body
- Response structure mismatch

**Recovery Strategy**: Fallback to empty state
- Recovery action: FALLBACK
- Error severity: MEDIUM
- Use cached or empty notifications
- Prevents application crash

**Edge Cases**:
- Partial response data
- Response with wrong content type
- Response structure changes breaking compatibility

### 4.5 Network Errors

**Error Type**: `API_NETWORK_ERROR`

**Handled Scenarios**:
- Network connectivity lost during request
- DNS resolution failures
- Request timeout
- Connection reset by peer

**Recovery Strategy**: Retry when network available
- Recovery action: RETRY
- Error severity: MEDIUM
- Maximum retries: 3
- Network state monitoring

**Edge Cases**:
- Network drops mid-request
- Slow network causing timeouts
- Network switches (WiFi to mobile)

---

## 5. Notification State and Processing Errors

### 5.1 Duplicate Notifications

**Error Type**: `NOTIFICATION_DUPLICATE`

**Handled Scenarios**:
- Same message received multiple times via PubSub
- API returns notifications already in store
- WebSocket and API delivering same notification
- Message ID collision

**Recovery Strategy**: Skip duplicate
- Recovery action: SKIP
- Error severity: LOW
- Duplicate detection by messageId
- Prevents duplicate UI notifications

**Edge Cases**:
- Duplicates with slightly different messageIds
- Duplicates from different sources (API + PubSub)
- Duplicates with same content but different IDs

### 5.2 Missing Notification Data

**Error Type**: `NOTIFICATION_MISSING_DATA`

**Handled Scenarios**:
- Notification received with null or undefined data
- Missing required fields (messageId, data)
- Empty notification payload
- Malformed notification structure

**Recovery Strategy**: Skip notification
- Recovery action: SKIP
- Error severity: MEDIUM
- Notification not added to store
- Error logged for debugging

**Edge Cases**:
- Notification with partial data
- Notification with data in unexpected format
- Notification missing critical fields

### 5.3 Display Failures

**Error Type**: `NOTIFICATION_DISPLAY_FAILED`

**Handled Scenarios**:
- Error processing notification for display
- Toast notification rendering fails
- UI component errors during notification display
- State update failures

**Recovery Strategy**: Skip display, keep in store
- Recovery action: SKIP
- Error severity: LOW
- Notification remains in store
- User can view in notifications panel

**Edge Cases**:
- Display fails for specific notification types
- UI errors preventing toast display
- State corruption during display

### 5.4 State Corruption

**Error Type**: `NOTIFICATION_STATE_CORRUPTED`

**Handled Scenarios**:
- Redux store state becomes inconsistent
- Notification data structure violations
- Unread count mismatch with notifications
- State update failures causing corruption

**Recovery Strategy**: Abort and reset state
- Recovery action: ABORT
- Error severity: HIGH
- State reset to initial values
- Requires re-fetch of notifications

**Edge Cases**:
- Partial state corruption
- Corruption during merge operations
- State corruption from concurrent updates

### 5.5 Initial Load Failures

**Error Type**: `INITIAL_LOAD_FAILED`

**Handled Scenarios**:
- Failed to fetch initial notifications from API
- API unavailable during application startup
- Network issues preventing initial load
- Authentication failures during initial load

**Recovery Strategy**: Retry with fallback
- Recovery action: RETRY
- Error severity: HIGH
- Maximum retries: 3
- Mark load complete even on failure to prevent blocking

**Edge Cases**:
- Initial load fails but PubSub messages arrive
- Partial initial load (some notifications, then error)
- Initial load timeout

### 5.6 Merge Failures

**Error Type**: `MERGE_FAILED`

**Handled Scenarios**:
- Failed to merge API notifications with existing state
- Redux dispatch errors during merge
- State update conflicts during merge
- Data structure incompatibility

**Recovery Strategy**: Fallback to replace operation
- Recovery action: FALLBACK
- Error severity: MEDIUM
- Replace existing notifications instead of merge
- Prevents data loss

**Edge Cases**:
- Merge fails for specific notification types
- Concurrent merge operations
- Merge with corrupted existing state

---

## 6. Edge Cases and Special Scenarios

### 6.1 No Messages Received

**Handled Scenarios**:
- PubSub subscription active but no messages arriving
- WebSocket connected but no notifications received
- Long periods without message activity
- Silent failures in message delivery

**Handling Strategy**:
- Connection health monitoring via heartbeats
- Periodic connection status checks
- Timeout detection for expected messages
- User notification if expected messages don't arrive

**Edge Cases**:
- Messages published but not delivered
- Subscription active but messages not reaching listener
- WebSocket connected but server not forwarding messages

### 6.2 Service Failures

**Handled Scenarios**:
- Backend notification service completely down
- Database unavailable preventing notification storage
- PubSub service outage
- WebSocket server crash

**Handling Strategy**:
- Graceful degradation to API-only mode
- Cached notifications displayed
- User notified of service issues
- Automatic retry when services recover
- Queue messages for processing when services return

**Edge Cases**:
- Partial service failure (some features work, others don't)
- Service recovers but with data loss
- Multiple services failing simultaneously

### 6.3 Concurrent Operations

**Handled Scenarios**:
- Multiple notification sources (API + PubSub) delivering simultaneously
- Rapid sequence of notifications
- State updates from multiple sources
- Race conditions in notification processing

**Handling Strategy**:
- Duplicate detection prevents duplicate processing
- Queue management for ordered processing
- State update batching where possible
- Initial load completion flag prevents race conditions

**Edge Cases**:
- API and PubSub deliver same notification simultaneously
- Notifications arrive faster than processing rate
- State updates conflict during concurrent operations

### 6.4 Timeout Scenarios

**Handled Scenarios**:
- Document extraction timeout (10 minutes)
- Initial load timeout (5 seconds for PubSub queuing)
- API request timeouts
- WebSocket connection timeout (20 seconds)

**Handling Strategy**:
- Timeout detection with appropriate actions
- User notifications for timeouts
- Cleanup of timed-out operations
- Retry mechanisms where appropriate

**Edge Cases**:
- Timeout occurs during critical operation
- Multiple timeouts in sequence
- Timeout false positives

### 6.5 Browser and Environment Issues

**Handled Scenarios**:
- localStorage unavailable (private browsing, quota exceeded)
- Browser tab backgrounded affecting WebSocket
- Page visibility changes
- Browser storage quota exceeded

**Handling Strategy**:
- Graceful fallback when localStorage fails
- Error handling for storage operations
- Connection management based on page visibility
- Storage quota monitoring

**Edge Cases**:
- localStorage read succeeds but write fails
- Partial localStorage data corruption
- Browser-specific WebSocket limitations

### 6.6 Message Ordering

**Handled Scenarios**:
- Messages arrive out of order
- Older messages arrive after newer ones
- Duplicate messages with different timestamps
- Messages with same timestamp

**Handling Strategy**:
- Timestamp-based sorting in UI
- Message ID tracking for ordering
- Unread notifications prioritized in display
- Duplicate detection prevents out-of-order duplicates

**Edge Cases**:
- Clock skew between systems
- Messages with identical timestamps
- Messages without timestamps

### 6.7 Large Message Volumes

**Handled Scenarios**:
- High frequency of notifications
- Large notification payloads
- Memory concerns with many notifications
- Performance degradation with large lists

**Handling Strategy**:
- Notification list limits (50 errors max in state)
- Pagination for API fetches
- Efficient state updates
- UI virtualization for large lists

**Edge Cases**:
- Sudden spike in notification volume
- Very large individual notification payloads
- Memory pressure from accumulated notifications

### 6.8 User Session Management

**Handled Scenarios**:
- User logs out during active notifications
- User switches accounts
- Session expires during notification processing
- Multiple tabs with same user

**Handling Strategy**:
- Authentication state checks before processing
- Cleanup on logout
- Per-tab connection management
- State reset on authentication change

**Edge Cases**:
- Logout during message processing
- Session expires mid-operation
- Notifications for logged-out user

---

## 7. Error Recovery Actions

### 7.1 RETRY
- **When Used**: Recoverable errors that may succeed on retry
- **Examples**: Connection failures, API timeouts, ack failures
- **Strategy**: Exponential backoff with maximum retry limits

### 7.2 SKIP
- **When Used**: Errors where skipping is safe and appropriate
- **Examples**: Duplicate messages, malformed data, missing user ID
- **Strategy**: Log error and continue processing other messages

### 7.3 QUEUE
- **When Used**: Temporary failures that may resolve soon
- **Examples**: Routing failures, emit failures, connection issues
- **Strategy**: Store message for later processing when conditions improve

### 7.4 FALLBACK
- **When Used**: Errors where alternative approach is available
- **Examples**: Invalid API response, merge failures
- **Strategy**: Use alternative data source or operation mode

### 7.5 ABORT
- **When Used**: Non-recoverable errors requiring intervention
- **Examples**: Missing subscription, authentication required, state corruption
- **Strategy**: Stop operation and require manual intervention or configuration fix

---

## 8. Error Severity Levels

### 8.1 CRITICAL
- **Impact**: System cannot function without resolution
- **Examples**: PubSub connection failed, subscription missing
- **Action**: Immediate attention required, may require configuration changes

### 8.2 HIGH
- **Impact**: Significant functionality impaired
- **Examples**: Socket reconnection failed, API service unavailable, initial load failed
- **Action**: Retry with aggressive strategy, user notification may be needed

### 8.3 MEDIUM
- **Impact**: Some functionality affected but system continues
- **Examples**: Message parse failed, routing failed, API fetch failed
- **Action**: Retry with standard strategy, log for monitoring

### 8.4 LOW
- **Impact**: Minor issues, minimal user impact
- **Examples**: Duplicate notification, missing user ID, display failed
- **Action**: Skip and continue, log for awareness

---

## 9. Monitoring and Observability

### 9.1 Error Tracking
- All errors logged with context and timestamps
- Error history maintained (max 100 entries)
- Errors categorized by type and severity
- Error counts and patterns tracked

### 9.2 Performance Monitoring
- Message processing times logged
- Connection state changes tracked
- Queue size and processing rate monitored
- API response times measured

### 9.3 User Experience
- User notifications for critical errors
- Toast messages for important failures
- Connection status indicators
- Graceful degradation when services unavailable

---

## 10. Best Practices Implemented

### 10.1 Defensive Programming
- Null/undefined checks throughout
- Type validation for incoming data
- Safe error handling with fallbacks
- Boundary condition handling

### 10.2 Resilience
- Automatic retry mechanisms
- Circuit breaker patterns for failing services
- Queue management for temporary failures
- State recovery mechanisms

### 10.3 User Experience
- Non-blocking error handling
- Clear user notifications
- Graceful degradation
- Transparent error recovery

### 10.4 Data Integrity
- Duplicate prevention
- State consistency checks
- Transaction-like operations where possible
- Data validation before processing

---

## Conclusion

This comprehensive error handling system ensures the notifications flow remains robust, resilient, and user-friendly even under adverse conditions. All error types are categorized, assigned appropriate recovery strategies, and monitored for continuous improvement of the system's reliability.



