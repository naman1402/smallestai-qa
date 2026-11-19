> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# Create Access Token (deprecated)

POST https://api.smallest.ai/waves/v1/auth/token
Content-Type: application/json

Deprecated. Use [`POST /console/v1/auth/token`](/api-reference/models/access-tokens/create-access-token)
instead. This endpoint still works, but a token it mints is valid only in the region
that minted it (`api.india.smallest.ai` or `api.us.smallest.ai`). The request body
and responses are the same as the console endpoint. It will be retired with advance
notice.


Reference: https://docs.smallest.ai/api-reference/models/access-tokens/create-access-token-deprecated

## Authentication

- `Authorization` header (required) (prefixed with ` Bearer  `) — API key authentication. Include your key as `Authorization: Bearer YOUR_API_KEY`. `POST /waves/v1/stt`, the text-to-speech endpoints and the speech WebSockets also accept short-lived access tokens; other endpoints need an API key. See [Token-based authentication](/api-reference/token-based-authentication).

## Request

### Body (application/json)

This endpoint expects a CreateAccessTokenRequest.

- `ttl_seconds` (integer, optional, default: 300) — How long the token stays valid, in seconds. Between 30 and 900. Defaults to 300 when omitted.

## Response

### 201

Token created. Valid only in the region that minted it.

- `access_token` (string, required) — The short-lived token. Always starts with `wat_`. Send it as `Authorization: Bearer <access_token>`.
- `token_type` (enum, required) — Always `Bearer`.
  - Allowed values: `Bearer`
- `expires_in` (integer, required) — Seconds until the token expires, equal to the `ttl_seconds` that was applied.
- `expires_at` (datetime, required) — Expiry time in UTC (ISO 8601).

## Errors

### 400 Bad Request Error

`ttl_seconds` is not an integer between 30 and 900.

- `status` (enum, optional)
  - Allowed values: `error`
- `message` (string, optional)
- `errors` (list of ValidationErrorResponseErrorsItems, optional) — One entry per failed field.

### 401 Unauthorized Error

Missing or invalid API key.

- `error` (string, optional)

### 403 Forbidden Error

The request was authenticated with an access token.

- `error` (string, optional)

## Types

### ValidationErrorResponseErrorsItems

- `code` (string, optional)
- `message` (string, optional)
- `path` (list of string, optional)

## Examples

**Request**

```json
{}
```

**Response**

```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 1,
  "expires_at": "2024-01-15T09:30:00Z"
}
```

**SDK Code**

```python
import requests

url = "https://api.smallest.ai/waves/v1/auth/token"

payload = {}
headers = {
    "Authorization": "Bearer <BearerAuth>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/waves/v1/auth/token';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer <BearerAuth>', 'Content-Type': 'application/json'},
  body: '{}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/waves/v1/auth/token"

	payload := strings.NewReader("{}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer <BearerAuth>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.smallest.ai/waves/v1/auth/token")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer <BearerAuth>'
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse<String> response = Unirest.post("https://api.smallest.ai/waves/v1/auth/token")
  .header("Authorization", "Bearer <BearerAuth>")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

```php
<?php
require_once('vendor/autoload.php');

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.smallest.ai/waves/v1/auth/token', [
  'body' => '{}',
  'headers' => [
    'Authorization' => 'Bearer <BearerAuth>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/auth/token");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer <BearerAuth>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer <BearerAuth>",
  "Content-Type": "application/json"
]
let parameters = [] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/auth/token")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```