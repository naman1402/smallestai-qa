> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# Get Pronunciation Dictionaries

GET https://api.smallest.ai/waves/v1/pronunciation-dicts

Retrieve all pronunciation dictionaries for the authenticated user

Reference: https://docs.smallest.ai/api-reference/models/text-to-speech/get-pronunciation-dicts

## Authentication

- `Authorization` header (required) (prefixed with ` Bearer  `) — API key authentication. Include your key as `Authorization: Bearer YOUR_API_KEY`. `POST /waves/v1/stt`, the text-to-speech endpoints and the speech WebSockets also accept short-lived access tokens; other endpoints need an API key. See [Token-based authentication](/api-reference/token-based-authentication).

## Response

### 200

List of pronunciation dictionaries

- `list of PronunciationDict`

## Errors

### 401 Unauthorized Error

Unauthorized - Invalid or missing authentication

- `error` (string, required) — Error message
- `details` (list of ErrorResponseDetailsItems, optional) — Additional error details (validation errors)

### 500 Internal Server Error

Internal server error

- `error` (string, required) — Error message
- `details` (list of ErrorResponseDetailsItems, optional) — Additional error details (validation errors)

## Types

### PronunciationDict

- `id` (string, required) — Unique identifier for the pronunciation dictionary
- `items` (list of PronunciationItem, required) — List of word-pronunciation pairs
- `createdAt` (datetime, required) — Timestamp when the dictionary was created

### ErrorResponseDetailsItems

### PronunciationItem

- `word` (string, required) — The word to be pronounced
- `pronunciation` (string, required) — The phonetic pronunciation of the word

## Examples

**Response**

```json
[
  {
    "id": "64f1234567890abcdef12345",
    "items": [
      {
        "word": "mysql",
        "pronunciation": "my-sequel"
      }
    ],
    "createdAt": "2023-09-01T12:00:00.000Z"
  }
]
```

**SDK Code**

```python Pronunciation Dictionaries_getPronunciationDicts_example
import requests

url = "https://api.smallest.ai/waves/v1/pronunciation-dicts"

headers = {"Authorization": "Bearer <BearerAuth>"}

response = requests.get(url, headers=headers)

print(response.json())
```

```javascript Pronunciation Dictionaries_getPronunciationDicts_example
const url = 'https://api.smallest.ai/waves/v1/pronunciation-dicts';
const options = {method: 'GET', headers: {Authorization: 'Bearer <BearerAuth>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Pronunciation Dictionaries_getPronunciationDicts_example
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/waves/v1/pronunciation-dicts"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <BearerAuth>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Pronunciation Dictionaries_getPronunciationDicts_example
require 'uri'
require 'net/http'

url = URI("https://api.smallest.ai/waves/v1/pronunciation-dicts")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer <BearerAuth>'

response = http.request(request)
puts response.read_body
```

```java Pronunciation Dictionaries_getPronunciationDicts_example
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse<String> response = Unirest.get("https://api.smallest.ai/waves/v1/pronunciation-dicts")
  .header("Authorization", "Bearer <BearerAuth>")
  .asString();
```

```php Pronunciation Dictionaries_getPronunciationDicts_example
<?php
require_once('vendor/autoload.php');

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.smallest.ai/waves/v1/pronunciation-dicts', [
  'headers' => [
    'Authorization' => 'Bearer <BearerAuth>',
  ],
]);

echo $response->getBody();
```

```csharp Pronunciation Dictionaries_getPronunciationDicts_example
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/pronunciation-dicts");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer <BearerAuth>");
IRestResponse response = client.Execute(request);
```

```swift Pronunciation Dictionaries_getPronunciationDicts_example
import Foundation

let headers = ["Authorization": "Bearer <BearerAuth>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/pronunciation-dicts")! as URL,
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