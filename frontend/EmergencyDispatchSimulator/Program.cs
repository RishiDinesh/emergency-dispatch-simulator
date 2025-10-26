using Blazored.LocalStorage;
using EmergencyDispatchSimulator.Api;
using EmergencyDispatchSimulator.Components;
using EmergencyDispatchSimulator.Services;
using MudBlazor;
using MudBlazor.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents()
    .AddHubOptions(options =>
    {
        options.MaximumReceiveMessageSize = long.MaxValue; // for js interop (large .wav)
    });

// Add MudBlazor
builder.Services.AddMudServices();
MudGlobal.InputDefaults.Variant = Variant.Outlined;
// MudGlobal.InputDefaults.Margin = Margin.Dense;
MudGlobal.Rounded = true;

// Add local storage
builder.Services.AddBlazoredLocalStorage();

// Add Emergency Dispatch Service API
builder.Services.AddScoped<IEdsApi, EdsApi>();

// Add web socket service as singleton
builder.Services.AddTransient<ChatWebSocketService>();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();


app.UseAntiforgery();

app.MapStaticAssets();
app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();