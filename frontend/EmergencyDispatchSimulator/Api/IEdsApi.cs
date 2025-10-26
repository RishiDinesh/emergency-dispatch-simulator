using EmergencyDispatchSimulator.Models;

namespace EmergencyDispatchSimulator.Api;

public interface IEdsApi
{
    Task CreateDispatchSimulation(ScenarioInputParameters parameters);
}

public class EdsApi : IEdsApi
{
    public async Task CreateDispatchSimulation(ScenarioInputParameters parameters)
    {
        // TODO
    }
}