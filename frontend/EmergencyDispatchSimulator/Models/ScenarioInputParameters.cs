namespace  EmergencyDispatchSimulator.Models;

public record ScenarioInputParameters
{
    public string? Incident { get; set; }
    public string? Location { get; set; }
    public string? Gender { get; set; }
    public string? Language { get; set; }
    public string? Emotion { get; set; }

    public string? GetParameter(string name) => name switch
    {
        ScenarioInputOptions.GroupCategory => Incident,
        ScenarioInputOptions.GroupLocation => Location,
        ScenarioInputOptions.GroupGender => Gender,
        ScenarioInputOptions.GroupLanguage => Language,
        ScenarioInputOptions.Emotion => Emotion,
        _ => null
    };

    public void SetParameter(string name, string value)
    {
        switch (name)
        {
            case ScenarioInputOptions.GroupCategory:
                Incident = value;
                break;
            case ScenarioInputOptions.GroupLocation:
                Location = value;
                break;
            case ScenarioInputOptions.GroupGender:
                Gender = value;
                break;
            case ScenarioInputOptions.GroupLanguage:
                Language = value;
                break;
            case ScenarioInputOptions.Emotion:
                Emotion = value;
                break;
        }
    }
}