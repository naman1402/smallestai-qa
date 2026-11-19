> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# Create Access Token

POST https://api.smallest.ai/console/v1/auth/token
Content-Type: application/json

Mint a short-lived access token from your API key. Call this from your server,
then hand the returned `access_token` to a browser or mobile client. The client
sends it as `Authorization: Bearer <access_token>` on TTS, STT and speech-to-speech
requests. On
WebSocket connections it can also go in the `api_key` query parameter. HTTP
requests must use the header.

A token works any number of times until it expires. It is accepted only on
TTS, STT and speech-to-speech inference routes: `POST /waves/v1/stt/`, `WSS /waves/v1/stt/live`,
`POST /waves/v1/tts`, `POST /waves/v1/tts/live`, `WSS /waves/v1/tts/live`, the
dedicated Lightning v3.1 routes (`POST /waves/v1/lightning-v3.1/get_speech`,
`POST /waves/v1/lightning-v3.1/stream`, `WSS /waves/v1/lightning-v3.1/get_speech/stream`),
`WSS /waves/v1/s2s`, and the voice-listing routes (public catalog, no cloned
voices). Treat any route not listed as unavailable to tokens. This endpoint,
`POST /waves/v1/pulse/get_text`, voice cloning, pronunciation dictionaries,
analytics and chat completions return `403` to a token.

Requests made with a token are billed to the API key that minted it. Deleting
that key invalidates its tokens. A token works in every region:
`api.smallest.ai`, `api.india.smallest.ai` (Mumbai) and `api.us.smallest.ai` (Oregon).

Send the API key as exactly `Authorization: Bearer <API key>`. This endpoint replaces
`POST /waves/v1/auth/token`, whose tokens work only in the region that minted them.

```bash
curl -X POST "https://api.smallest.ai/console/v1/auth/token" \
  -H "Authorization: Bearer $SMALLEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"ttl_seconds": 300}'
```

See the [Authentication guide](/api-reference/token-based-authentication)
for the end-to-end server and client flow.

Reference: https://docs.smallest.ai/api-reference/models/access-tokens/create-access-token

## Authentication

- `Authorization` header (required) (prefixed with ` Bearer  `) — API key authentication. Include your key as `Authorization: Bearer YOUR_API_KEY`. `POST /waves/v1/stt`, the text-to-speech endpoints and the speech WebSockets also accept short-lived access tokens; other endpoints need an API key. See [Token-based authentication](/api-reference/token-based-authentication).

## Request

### Body (application/json)

This endpoint expects a CreateAccessTokenRequest.

- `ttl_seconds` (integer, optional, default: 300) — How long the token stays valid, in seconds. Between 30 and 900. Defaults to 300 when omitted.

## Response

### 201

Token created.

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

The request was authenticated with an access token or an admin `X-API-Key` (only an API key can mint tokens), or the account, its email domain or its organization is blocked.

- `error` (string, optional)

### 429 Too Many Requests Error

Too many mint requests. Mint one token per client session and retry after a short wait.

- `error` (string, optional)

### 503 Service Unavailable Error

Temporarily unavailable. Retry with backoff.

- `error` (string, optional)

## Types

### ValidationErrorResponseErrorsItems

- `code` (string, optional)
- `message` (string, optional)
- `path` (list of string, optional)

## Examples

**Request**

```json
{
  "ttl_seconds": 300
}
```

**Response**

```json
{
  "access_token": "wat_...",
  "token_type": "Bearer",
  "expires_in": 300,
  "expires_at": "2026-09-22T13:01:14.533Z"
}
```

**SDK Code**

```python auth_create_access_token_example
import requests

url = "https://api.smallest.ai/console/v1/auth/token"

payload = { "ttl_seconds": 300 }
headers = {
    "Authorization": "Bearer <BearerAuth>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

```javascript auth_create_access_token_example
const url = 'https://api.smallest.ai/console/v1/auth/token';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer <BearerAuth>', 'Content-Type': 'application/json'},
  body: '{"ttl_seconds":300}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go auth_create_access_token_example
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/console/v1/auth/token"

	payload := strings.NewReader("{\n  \"ttl_seconds\": 300\n}")

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

```ruby auth_create_access_token_example
require 'uri'
require 'net/http'

url = URI("https://api.smallest.ai/console/v1/auth/token")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer <BearerAuth>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"ttl_seconds\": 300\n}"

response = http.request(request)
puts response.read_body
```

```java auth_create_access_token_example
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse<String> response = Unirest.post("https://api.smallest.ai/console/v1/auth/token")
  .header("Authorization", "Bearer <BearerAuth>")
  .header("Content-Type", "application/json")
  .body("{\n  \"ttl_seconds\": 300\n}")
  .asString();
```

```php auth_create_access_token_example
<?php
require_once('vendor/autoload.php');

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.smallest.ai/console/v1/auth/token', [
  'body' => '{
  "ttl_seconds": 300
}',
  'headers' => [
    'Authorization' => 'Bearer <BearerAuth>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp auth_create_access_token_example
using RestSharp;

var client = new RestClient("https://api.smallest.ai/console/v1/auth/token");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer <BearerAuth>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"ttl_seconds\": 300\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift auth_create_access_token_example
import Foundation

let headers = [
  "Authorization": "Bearer <BearerAuth>",
  "Content-Type": "application/json"
]
let parameters = ["ttl_seconds": 300] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/console/v1/auth/token")! as URL,
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