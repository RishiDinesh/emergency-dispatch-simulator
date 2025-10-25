using System.Net.WebSockets;
using System.Text;

namespace EmergencyDispatchSimulator.Services;

// Define the delegate for the event handler
public delegate void MessageReceivedHandler(string message);

public class ChatWebSocketService : IDisposable
{
    private readonly Uri _webSocketUri;
    private ClientWebSocket _ws;
    private CancellationTokenSource _cts;

    // Event components can subscribe to for real-time updates
    public event MessageReceivedHandler MessageReceived;

    public bool IsConnected => _ws?.State == WebSocketState.Open;

    // Replace with your external WebSocket API URL
    private const string ExternalApiUrl = "ws://localhost:8000/ws"; 
    
    public ChatWebSocketService()
    {
        _webSocketUri = new Uri(ExternalApiUrl);
        _ws = new ClientWebSocket();
        _cts = new CancellationTokenSource();
    }

    public async Task ConnectAsync()
    {
        if (IsConnected) return;

        try
        {
            // Connect to the external WebSocket API
            await _ws.ConnectAsync(_webSocketUri, CancellationToken.None);
            
            // Start the receive loop in the background
            _ = Task.Run(() => ReceiveLoop());
        }
        catch (WebSocketException ex)
        {
            // Handle connection errors (e.g., API is down)
            Console.WriteLine($"WebSocket connection error: {ex.Message}");
            MessageReceived?.Invoke($"[SYSTEM] Connection failed. Is API running? Error: {ex.Message}");
        }
    }

    private async Task ReceiveLoop()
    {
        // Use a large buffer size for receiving messages
        var buffer = new byte[1024 * 4];
        
        try
        {
            while (!_cts.IsCancellationRequested && _ws.State == WebSocketState.Open)
            {
                // Receive message segment
                var result = await _ws.ReceiveAsync(
                    new ArraySegment<byte>(buffer), 
                    _cts.Token);

                // Check if the connection was closed by the remote host
                if (result.MessageType == WebSocketMessageType.Close)
                {
                    await _ws.CloseOutputAsync(
                        WebSocketCloseStatus.NormalClosure,
                        "Closing", 
                        CancellationToken.None);
                    MessageReceived?.Invoke("[SYSTEM] Connection closed by remote server.");
                    break;
                }
                
                // Decode the message and fire the event
                var message = Encoding.UTF8.GetString(buffer, 0, result.Count);
                MessageReceived?.Invoke(message);

                // If message is incomplete, continue reading until EndOfMessage is true (not implemented here for simplicity)
            }
        }
        catch (OperationCanceledException)
        {
            // Expected when CancellationTokenSource is cancelled
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error in receive loop: {ex.Message}");
            MessageReceived?.Invoke($"[SYSTEM] Disconnected due to an error: {ex.Message}");
        }
    }

    public async Task SendAsync(string message)
    {
        if (IsConnected)
        {
            try
            {
                var bytes = Encoding.UTF8.GetBytes(message);
                var segment = new ArraySegment<byte>(bytes);
                
                // Send the message to the external API
                await _ws.SendAsync(
                    segment, 
                    WebSocketMessageType.Text, 
                    endOfMessage: true, 
                    CancellationToken.None);
                    
                // Optionally, update the UI to show the sent message immediately
                MessageReceived?.Invoke($"[YOU] {message}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error sending message: {ex.Message}");
                MessageReceived?.Invoke($"[SYSTEM] Failed to send message: {ex.Message}");
            }
        }
        else
        {
            MessageReceived?.Invoke("[SYSTEM] Cannot send: Not connected.");
        }
    }

    public void Dispose()
    {
        _cts.Cancel();
        if (_ws?.State == WebSocketState.Open || _ws?.State == WebSocketState.Connecting)
        {
             // Close the connection gracefully (non-blocking)
            _ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "Client closing", CancellationToken.None).Wait();
        }
        _ws?.Dispose();
        _cts?.Dispose();
    }
}
