> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# Update Pronunciation Dictionary

PUT https://api.smallest.ai/waves/v1/pronunciation-dicts
Content-Type: application/json

Update an existing pronunciation dictionary for the authenticated user

Reference: https://docs.smallest.ai/api-reference/models/text-to-speech/update-pronunciation-dict

## Authentication

- `Authorization` header (required) (prefixed with ` Bearer  `) — API key authentication. Include your key as `Authorization: Bearer YOUR_API_KEY`. `POST /waves/v1/stt`, the text-to-speech endpoints and the speech WebSockets also accept short-lived access tokens; other endpoints need an API key. See [Token-based authentication](/api-reference/token-based-authentication).

## Request

### Body (application/json)

This endpoint expects an UpdatePronunciationDictRequest.

- `id` (string, required) — ID of the pronunciation dictionary to update
- `items` (list of PronunciationItem, required) — Updated list of word-pronunciation pairs

## Response

### 200

Successfully updated pronunciation dictionary

- `id` (string, required) — ID of the updated pronunciation dictionary
- `items` (list of PronunciationItem, required) — Updated list of word-pronunciation pairs

## Errors

### 400 Bad Request Error

Bad request - Invalid request body

- `error` (string, required) — Error message
- `details` (list of ErrorResponseDetailsItems, optional) — Additional error details (validation errors)

### 401 Unauthorized Error

Unauthorized - Invalid or missing authentication

- `error` (string, required) — Error message
- `details` (list of ErrorResponseDetailsItems, optional) — Additional error details (validation errors)

### 500 Internal Server Error

Internal server error

- `error` (string, required) — Error message
- `details` (list of ErrorResponseDetailsItems, optional) — Additional error details (validation errors)

## Types

### PronunciationItem

- `word` (string, required) — The word to be pronounced
- `pronunciation` (string, required) — The phonetic pronunciation of the word

### ErrorResponseDetailsItems

## Examples

**Request**

```json
{
  "id": "64f1234567890abcdef12345",
  "items": [
    {
      "word": "mysql",
      "pronunciation": "my-sequel"
    }
  ]
}
```

**Response**

```json
{
  "id": "64f1234567890abcdef12345",
  "items": [
    {
      "word": "mysql",
      "pronunciation": "my-sequel"
    },
    {
      "word": "goodbye",
      "pronunciation": "goodbai"
    }
  ]
}
```

**SDK Code**

```python Pronunciation Dictionaries_updatePronunciationDict_example
import requests

url = "https://api.smallest.ai/waves/v1/pronunciation-dicts"

payload = {
    "id": "64f1234567890abcdef12345",
    "items": [
        {
            "word": "mysql",
            "pronunciation": "my-sequel"
        }
    ]
}
headers = {
    "Authorization": "Bearer <BearerAuth>",
    "Content-Type": "application/json"
}

response = requests.put(url, json=payload, headers=headers)

print(response.json())
```

```javascript Pronunciation Dictionaries_updatePronunciationDict_example
const url = 'https://api.smallest.ai/waves/v1/pronunciation-dicts';
const options = {
  method: 'PUT',
  headers: {Authorization: 'Bearer <BearerAuth>', 'Content-Type': 'application/json'},
  body: '{"id":"64f1234567890abcdef12345","items":[{"word":"mysql","pronunciation":"my-sequel"}]}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Pronunciation Dictionaries_updatePronunciationDict_example
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/waves/v1/pronunciation-dicts"

	payload := strings.NewReader("{\n  \"id\": \"64f1234567890abcdef12345\",\n  \"items\": [\n    {\n      \"word\": \"mysql\",\n      \"pronunciation\": \"my-sequel\"\n    }\n  ]\n}")

	req, _ := http.NewRequest("PUT", url, payload)

	req.Header.Add("Authorization", "Bearer <BearerAuth>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Pronunciation Dictionaries_updatePronunciationDict_example
require 'uri'
require 'net/http'

url = URI("https://api.smallest.ai/waves/v1/pronunciation-dicts")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Put.new(url)
request["Authorization"] = 'Bearer <BearerAuth>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"id\": \"64f1234567890abcdef12345\",\n  \"items\": [\n    {\n      \"word\": \"mysql\",\n      \"pronunciation\": \"my-sequel\"\n    }\n  ]\n}"

response = http.request(request)
puts response.read_body
```

```java Pronunciation Dictionaries_updatePronunciationDict_example
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse<String> response = Unirest.put("https://api.smallest.ai/waves/v1/pronunciation-dicts")
  .header("Authorization", "Bearer <BearerAuth>")
  .header("Content-Type", "application/json")
  .body("{\n  \"id\": \"64f1234567890abcdef12345\",\n  \"items\": [\n    {\n      \"word\": \"mysql\",\n      \"pronunciation\": \"my-sequel\"\n    }\n  ]\n}")
  .asString();
```

```php Pronunciation Dictionaries_updatePronunciationDict_example
<?php
require_once('vendor/autoload.php');

$client = new \GuzzleHttp\Client();

$response = $client->request('PUT', 'https://api.smallest.ai/waves/v1/pronunciation-dicts', [
  'body' => '{
  "id": "64f1234567890abcdef12345",
  "items": [
    {
      "word": "mysql",
      "pronunciation": "my-sequel"
    }
  ]
}',
  'headers' => [
    'Authorization' => 'Bearer <BearerAuth>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp Pronunciation Dictionaries_updatePronunciationDict_example
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/pronunciation-dicts");
var request = new RestRequest(Method.PUT);
request.AddHeader("Authorization", "Bearer <BearerAuth>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"id\": \"64f1234567890abcdef12345\",\n  \"items\": [\n    {\n      \"word\": \"mysql\",\n      \"pronunciation\": \"my-sequel\"\n    }\n  ]\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift Pronunciation Dictionaries_updatePronunciationDict_example
import Foundation

let headers = [
  "Authorization": "Bearer <BearerAuth>",
  "Content-Type": "application/json"
]
let parameters = [
  "id": "64f1234567890abcdef12345",
  "items": [
    [
      "word": "mysql",
      "pronunciation": "my-sequel"
    ]
  ]
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/pronunciation-dicts")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "PUT"
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