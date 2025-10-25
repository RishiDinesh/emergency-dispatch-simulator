using System.Net.WebSockets;
using System.Text;

namespace EmergencyDispatchSimulator.Services;

// for event handler
public delegate Task MessageReceivedHandler(string message);

public class ChatWebSocketService : IAsyncDisposable
{
    private readonly Uri _webSocketUri;
    private readonly ClientWebSocket _ws;
    private readonly CancellationTokenSource _cts;

    // Event components can subscribe to for real-time updates
    public event MessageReceivedHandler MessageReceived;
    public event Action<string> StatusChanged;

    public bool IsConnected => _ws?.State == WebSocketState.Open;

    private const string ExternalApiUrl = "ws://localhost:8000/ws"; 
    
    public ChatWebSocketService()
    {
        _webSocketUri = new Uri(ExternalApiUrl);
        _ws = new ClientWebSocket();
        _cts = new CancellationTokenSource();
    }

    public async Task ConnectAsync()
    {
        if (IsConnected) 
            return;

        try
        {
            // Connect to the external WebSocket API
            await _ws.ConnectAsync(_webSocketUri, CancellationToken.None);
            
            // Start receive loop in the background
            _ = Task.Run(ReceiveLoop);
        }
        catch (WebSocketException ex)
        {
            // Handle connection errors (e.g., API is down)
            Console.WriteLine($"WebSocket connection error: {ex.Message}");
            StatusChanged?.Invoke($"[SYSTEM] Connection failed. Is API running? Error: {ex.Message}");
        }
    }

    private async Task ReceiveLoop()
    {
        // Use a large buffer size for receiving messages
        var buffer = new byte[1024 * 64];
        using var stream = new MemoryStream();
        
        try
        {
            while (!_cts.IsCancellationRequested && _ws.State == WebSocketState.Open)
            {
                WebSocketReceiveResult result;
                stream.Position = 0;
                stream.SetLength(0); // Clear the stream for a new message

                do
                { 
                    // Receive message segment
                    result = await _ws.ReceiveAsync(new ArraySegment<byte>(buffer), _cts.Token);
                    
                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        StatusChanged?.Invoke("[SYSTEM] Connection closed by remote server.");
                        return; 
                    }

                    stream.Write(buffer, 0, result.Count);
                } while (!result.EndOfMessage);

                var byteArray = stream.ToArray();
                var b64Str = Convert.ToBase64String(byteArray);
                
                MessageReceived?.Invoke(b64Str);
            }
        }
        catch (OperationCanceledException)
        {
            // when CancellationTokenSource is cancelled
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error in receive loop: {ex.Message}");
            StatusChanged?.Invoke($"[SYSTEM] Disconnected due to an error: {ex.Message}");
        }
    }

    public async Task SendAsync(string message)
    {
        if (!IsConnected)
        {
            StatusChanged?.Invoke("[SYSTEM] Cannot send: Not connected.");
            return;
        }
        
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
                
            // update the UI to show the sent message immediately
            // MessageReceived?.Invoke($"[YOU] {message}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error sending message: {ex.Message}");
            StatusChanged?.Invoke($"[SYSTEM] Failed to send message: {ex.Message}");
        }
    }

    public async ValueTask DisposeAsync()
    {
        await _cts.CancelAsync();
        if (_ws?.State is WebSocketState.Open or WebSocketState.Connecting)
        {
             // close gracefully (non-blocking)
            await _ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "Client closing", CancellationToken.None);
        }
        _ws?.Dispose();
        _cts?.Dispose();
    }
}
