namespace EmergencyDispatchSimulator.Models;

/// <summary>
/// Holds all available options for creating a scenario.
/// </summary>
public static class ScenarioInputOptions
{
    // group names of parameters
    public const string GroupCategory = "incident_category";
    public const string GroupLocation = "location_type";
    public const string GroupGender = "gender";
    public const string GroupLanguage = "language";
    public const string Emotion = "emotion";

    // groupings of parameters
    public static Dictionary<string, ScenarioInputOption> GetAvailableOptions()
    {
        List<ScenarioInputOption> options = 
        [
            new()
            {
                Name = GroupCategory,
                Label = "Incident",
                Description = "The type of emergency or incident that is occurring",
                Options = [
                    "medical_non_trauma", "trauma_injury", "behavioral_crisis", "overdose_poisoning",
                    "obstetrics_childbirth",
                    "fire_structure", "fire_vehicle", "fire_wildland", "explosion", "smoke_co_alarm", "gas_leak_hazmat",
                    "electrical_utility", "traffic_collision_minor", "traffic_collision_major", "pedestrian_struck",
                    "cyclist_struck", "vehicle_rollover", "hit_and_run", "public_transport_incident",
                    "water_rescue_drowning",
                    "ice_rescue", "search_and_rescue_missing_person", "building_collapse", "entrapment_confined_space",
                    "animal_incident", "suspicious_person_vehicle", "burglary_in_progress", "robbery_in_progress",
                    "theft_larceny", "assault_in_progress", "domestic_dispute_violence", "sexual_assault", "shots_fired",
                    "stabbing_cutting", "active_violence_active_shooter", "hostage_barricade", "arson_suspected",
                    "vandalism_property_damage", "civil_disturbance_riot", "disorderly_conduct_noise", "trespass",
                    "welfare_check", "abduction_kidnapping", "suspicious_package", "bomb_threat",
                    "power_outage_infrastructure",
                    "road_hazard_debris", "weather_disaster", "aviation_incident", "train_derailment", "marine_incident",
                    "unknown_trouble_911_hangup", "prank_false_call", "alarm_panic_holdup", "alarm_burglar", "alarm_fire"
                ]
            },
            new(){
                Name = GroupLocation,
                Label = "Location",
                Description = "The environment or setting where the incident is taking place",
                Options = [
                    "house", "apartment", "street", "highway", "business", "school", "park", "rural", "highrise", "transit",
                    "waterfront"
                ]
            },
            new()
            {
                Name = GroupGender, 
                Label = "Gender",
                Description = "The gender of the person reporting the incident",
                Options = ["male", "female"]
            },
            new()
            {
                Name = GroupLanguage,
                Label = "Language",
                Description = "The language being spoken by the person reporting the emergency",
                Options = 
                [
                    "English", "Spanish", "French", "Mandarin", "Cantonese", "Arabic", "Hindi", "Punjabi", "Vietnamese",
                    "Portuguese", "Russian"
                ]
            },
            new()
            {
                Name = Emotion, 
                Label = "Emotion",
                Description = "The emotional state of the person reporting the emergency",
                Options = ["anger", "sad", "fear", "neutral"]
            }
        ];

        return options.ToDictionary(x => x.Name, x => x);
    }
    
}


public record ScenarioInputOption
{
    public required string Name { get; init; }
    public required string Label { get; init; }
    public required string Description { get; init; }
    public required List<string> Options { get; init; }
}