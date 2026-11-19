> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# List Voice Clones

GET https://api.smallest.ai/waves/v1/voice-cloning

Retrieve all voice clones in your organization.


Reference: https://docs.smallest.ai/api-reference/models/text-to-speech/list-voice-clones

## Authentication

- `Authorization` header (required) (prefixed with ` Bearer  `) — API key authentication. Include your key as `Authorization: Bearer YOUR_API_KEY`. `POST /waves/v1/stt`, the text-to-speech endpoints and the speech WebSockets also accept short-lived access tokens; other endpoints need an API key. See [Token-based authentication](/api-reference/token-based-authentication).

## Response

### 200

List of voice clones.

- `data` (list of WavesV1VoiceCloningGetResponsesContentApplicationJsonSchemaDataItems, optional)

## Errors

### 401 Unauthorized Error

Unauthorized.

- `any`

### 500 Internal Server Error

Server error.

- `any`

## Types

### WavesV1VoiceCloningGetResponsesContentApplicationJsonSchemaDataItems

- `_id` (string, optional)
- `voiceId` (string, optional)
- `displayName` (string, optional)
- `description` (string, optional)
- `accent` (string, optional)
- `tags` (list of string, optional)
- `language` (string, optional)
- `status` (enum, optional)
  - Allowed values: `pending`, `processing`, `completed`, `failed`
- `cloningType` (enum, optional)
  - Allowed values: `instant`, `professional`
- `modelIds` (list of string, optional) — Models this clone is compatible with. `lightning-v3.1` is the current default. Older entries may list `lightning-large`.
- `createdAt` (datetime, optional)

## Examples

**Response**

```json
{
  "data": [
    {
      "_id": "string",
      "voiceId": "voice_dLP5T67Qw7",
      "displayName": "string",
      "description": "string",
      "accent": "string",
      "tags": [
        "string"
      ],
      "language": "string",
      "status": "pending",
      "cloningType": "instant",
      "modelIds": [
        "string"
      ],
      "createdAt": "2024-01-15T09:30:00Z"
    }
  ]
}
```

**SDK Code**

```python
import requests

url = "https://api.smallest.ai/waves/v1/voice-cloning"

headers = {"Authorization": "Bearer <BearerAuth>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/waves/v1/voice-cloning';
const options = {method: 'GET', headers: {Authorization: 'Bearer <BearerAuth>'}};

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
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/waves/v1/voice-cloning"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <BearerAuth>")

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

url = URI("https://api.smallest.ai/waves/v1/voice-cloning")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer <BearerAuth>'

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse<String> response = Unirest.get("https://api.smallest.ai/waves/v1/voice-cloning")
  .header("Authorization", "Bearer <BearerAuth>")
  .asString();
```

```php
<?php
require_once('vendor/autoload.php');

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.smallest.ai/waves/v1/voice-cloning', [
  'headers' => [
    'Authorization' => 'Bearer <BearerAuth>',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/voice-cloning");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer <BearerAuth>");
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer <BearerAuth>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/voice-cloning")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

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