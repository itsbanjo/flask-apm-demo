using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;

namespace OtelApp.Extensions;

public static class TelemetryExtensions
{
    public static IServiceCollection AddApplicationTelemetry(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        var resourceBuilder = ResourceBuilder.CreateDefault()
            .AddService("frontend-otel-dotnet", serviceVersion: "1.0")
            .AddTelemetrySdk()
            .AddAttributes(new Dictionary<string, object>
            {
                ["deployment.environment"] = configuration["ASPNETCORE_ENVIRONMENT"] ?? "Production"
            });

        services.AddOpenTelemetry()
            .ConfigureResource(r => r.AddResource(resourceBuilder))
            .WithTracing(builder => ConfigureTracing(builder, configuration))
            .WithMetrics(builder => ConfigureMetrics(builder, configuration));

        return services;
    }

    private static TracerProviderBuilder ConfigureTracing(
        TracerProviderBuilder builder,
        IConfiguration configuration)
    {
        return builder
            .AddAspNetCoreInstrumentation(options =>
            {
                options.RecordException = true;
                options.EnrichWithHttpRequest = (activity, httpRequest) =>
                {
                    activity.SetTag("custom.http.request.header.x-high-latency",
                        httpRequest.Headers["X-High-Latency"].ToString());
                };
            })
            .AddHttpClientInstrumentation()
            .AddProcessInstrumentation()
            .AddRuntimeInstrumentation()
            .AddOtlpExporter(opts =>
            {
                opts.Endpoint = new Uri(configuration["Otlp:Endpoint"] 
                    ?? "http://otel-collector:4317");
            });
    }

    private static MeterProviderBuilder ConfigureMetrics(
        MeterProviderBuilder builder,
        IConfiguration configuration)
    {
        return builder
            .AddAspNetCoreInstrumentation()
            .AddHttpClientInstrumentation()
            .AddProcessInstrumentation()
            .AddRuntimeInstrumentation()
            .AddMeter(OrderMetrics.MeterName)
            .AddOtlpExporter(opts =>
            {
                opts.Endpoint = new Uri(configuration["Otlp:Endpoint"] 
                    ?? "http://otel-collector:4317");
            });
    }
}
