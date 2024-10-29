using System.Text.Json;

namespace OtelApp.Services;

public class BackendService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<BackendService> _logger;
    private readonly string _baseUrl;

    public BackendService(
        HttpClient httpClient,
        ILogger<BackendService> logger,
        IConfiguration configuration)
    {
        _httpClient = httpClient;
        _logger = logger;
        _baseUrl = configuration["BackendService:BaseUrl"] ?? "http://backend:5002";
    }

    public async Task<OrderResponse> ProcessOrderAsync(OrderRequest request, string transactionId)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync(
                $"{_baseUrl}/process_order",
                new
                {
                    transaction_id = transactionId,
                    user_id = request.UserId,
                    product_id = request.ProductId,
                    product_name = request.ProductName,
                    quantity = request.Quantity,
                    price = request.Price
                });

            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<OrderResponse>() 
                ?? throw new Exception("Invalid response from backend");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing order {TransactionId}", transactionId);
            throw;
        }
    }
}
