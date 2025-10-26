using EmergencyDispatchSimulator.Models;

namespace EmergencyDispatchSimulator.Api;

public interface IEdsApi
{
    Task CreateDispatchSimulation(ScenarioInputParameters parameters);
}

public class EdsApi : IEdsApi
{

    private readonly HttpClient _http;
    
    public EdsApi()
    {
        var apiUrl = Environment.GetEnvironmentVariable("BACKEND_API_URL")
                             ?? throw new ArgumentNullException("BACKEND_API_URL");
        Console.WriteLine($"Api url set to {apiUrl}");
        
        _http = new()
        {
            BaseAddress = new Uri(apiUrl)
        };
    }
    
    
    public async Task CreateDispatchSimulation(ScenarioInputParameters parameters)
    {
        using var formContent = new MultipartFormDataContent();
        formContent.Add(new StringContent(parameters.Incident ?? string.Empty), "incident");
        formContent.Add(new StringContent(parameters.Location ?? string.Empty), "location");
        formContent.Add(new StringContent(parameters.Emotion ?? string.Empty), "emotion");
        formContent.Add(new StringContent(parameters.Gender ?? string.Empty), "gender");
        formContent.Add(new StringContent(parameters.Language ?? string.Empty), "language");
        
        var response = await _http.PostAsync("/submit_form", formContent);
        Console.WriteLine($"CreateDispatchSimulation returned response {response.StatusCode}");
        response.EnsureSuccessStatusCode();
    }
}