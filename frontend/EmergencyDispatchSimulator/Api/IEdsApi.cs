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
                             ?? "http://localhost:8000";
        Console.WriteLine($"Api url set to {apiUrl}");
        
        _http = new()
        {
            BaseAddress = new Uri(apiUrl)
        };
    }
    
    
    public async Task CreateDispatchSimulation(ScenarioInputParameters parameters)
    {
        // TODO
        var response = await _http.GetAsync("/");
        Console.WriteLine($"DONE with response {response.StatusCode}");
    }
}