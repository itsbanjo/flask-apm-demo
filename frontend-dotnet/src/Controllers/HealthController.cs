using Microsoft.AspNetCore.Mvc;

namespace OtelApp.Controllers;

[ApiController]
[Route("[controller]")]
public class HealthController : ControllerBase
{
    private readonly ILogger<HealthController> _logger;

    public HealthController(ILogger<HealthController> logger)
    {
        _logger = logger;
    }

    [HttpGet("/health")]
    public IActionResult Check()
    {
        _logger.LogInformation("Health check requested");
        return Ok(new { status = "healthy" });
    }

    [HttpGet("/simulate-error")]
    public IActionResult SimulateError()
    {
        _logger.LogError("Simulated error occurred");
        throw new Exception("This is a simulated error");
    }

    [HttpGet("/simulate-slow-request")]
    public async Task<IActionResult> SimulateSlowRequest()
    {
        using var activity = System.Diagnostics.Activity.Current;
        activity?.SetTag("slow_request", true);

        _logger.LogInformation("Starting slow request simulation");
        await Task.Delay(5000);
        _logger.LogInformation("Completed slow request simulation");

        return Ok("Slow request completed");
    }
}
