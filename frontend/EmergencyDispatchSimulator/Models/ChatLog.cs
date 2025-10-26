namespace EmergencyDispatchSimulator.Models;


public record ChatLog
{
    public List<ChatLogItem> data { get; set; }
}

public record ChatLogItem
{
    public string role { get; set; }
    public double timestamp { get; set; }
    public string transcription { get; set; }
    public string audio { get; set; }
}