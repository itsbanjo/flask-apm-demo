# Use .NET 8 SDK for building
FROM mcr.microsoft.com/dotnet/sdk:8.0-jammy AS build
WORKDIR /src

# Copy csproj and restore dependencies
COPY *.csproj ./
RUN dotnet restore

# Copy everything else and build
COPY . ./
RUN dotnet publish -c Release -o /app

# Build runtime image
FROM mcr.microsoft.com/dotnet/aspnet:8.0-jammy
WORKDIR /app
COPY --from=build /app .

# Enable OpenTelemetry
ENV ASPNETCORE_ENVIRONMENT=Production
ENV OTEL_DOTNET_AUTO_HOME=/app
ENV OTEL_DOTNET_AUTO_PLUGINS="AspNetCore,HttpClient,Runtime"
ENV OTEL_SERVICE_NAME=frontend-otel-dotnet
ENV OTEL_RESOURCE_ATTRIBUTES=deployment.environment=production

EXPOSE 8080
ENTRYPOINT ["dotnet", "OtelApp.dll"]
