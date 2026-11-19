> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# Get Voices

GET https://api.smallest.ai/waves/v1/{model}/get_voices

Return the voice catalog for the chosen Lightning v3.1 pool. Two pools:

- `lightning-v3.1`: the Standard catalog. Retiring on Nov 30, 2026; use `lightning-v3.1-pro`.
- `lightning-v3.1-pro` — the Pro catalog. Curated set across American, British, and Indian accents plus 29 additional languages. Same latency and concurrency as Standard, on dedicated inference.

The endpoint is pool-scoped: `/waves/v1/lightning-v3.1/get_voices` returns Standard voices only; `/waves/v1/lightning-v3.1-pro/get_voices` returns Pro voices only. Call one or both depending on which pool you plan to use.

Each voice carries tags (`language`, `accent`, `gender`, `age`, `emotions`, `usecases`). Filter client-side to find the voices that match a target language, accent, or use case. Pass the returned `voiceId` as `voice_id` on the unified [`POST /waves/v1/tts`](/api-reference/models/text-to-speech/synthesize-speech) route, together with `"model": "lightning_v3.1"` (Standard), `"model": "lightning_v3.1_pro"` (Pro) or `"model": "lightning_v3.1_pro_10_26"` (Pro voices on the [preview checkpoint](/model-cards/text-to-speech/lightning-v-3-1-pro#checkpoints) for English, Spanish and Hindi).

For the canonical per-language voice list (with previews and recommended pairings), see the [Lightning v3.1](/model-cards/text-to-speech/lightning-v-3-1) and [Lightning v3.1 Pro](/model-cards/text-to-speech/lightning-v-3-1-pro) model cards.


Reference: https://docs.smallest.ai/api-reference/models/text-to-speech/get-waves-voices

## Request

### Path parameters

- `model` (enum, required, default: lightning-v3.1) — The pool to query. `lightning-v3.1` returns Standard voices; `lightning-v3.1-pro` returns Pro voices. Note the hyphenated path form differs from the underscored body form used on `POST /waves/v1/tts` (`lightning_v3.1`, `lightning_v3.1_pro`).
  - Allowed values: `lightning-v3.1`, `lightning-v3.1-pro`

## Response

### 200

Voices retrieved successfully.

- `voices` (list of WavesV1ModelGetVoicesGetResponsesContentApplicationJsonSchemaVoicesItems, optional) — List of available voices for the chosen pool.

## Errors

### 400 Bad Request Error

Bad request. The most common cause is a `{model}` value outside the enum. Use `lightning-v3.1` or `lightning-v3.1-pro`.

- `error` (string, optional) — Error type
- `message` (string, optional) — Error message

### 401 Unauthorized Error

Missing or invalid API key.

- `error` (string, optional) — Error type
- `message` (string, optional) — Error message

### 500 Internal Server Error

Server error.

- `error` (string, optional) — Error type
- `message` (string, optional) — Error message

## Types

### WavesV1ModelGetVoicesGetResponsesContentApplicationJsonSchemaVoicesItems

- `voiceId` (string, required) — Unique voice identifier. Pass this value as `voice_id` on `POST /waves/v1/tts` (or the streaming route).
- `displayName` (string, required) — Human-readable name for the voice.
- `tags` (WavesV1ModelGetVoicesGetResponsesContentApplicationJsonSchemaVoicesItemsTags, optional) — Metadata describing the voice. Filter client-side to find voices for a target language, accent, or use case. Fields may be empty on some voices.

### WavesV1ModelGetVoicesGetResponsesContentApplicationJsonSchemaVoicesItemsTags

Metadata describing the voice. Filter client-side to find voices for a target language, accent, or use case. Fields may be empty on some voices.

- `language` (list of string, optional) — Languages the voice was trained on (e.g. `["english"]`, `["english", "hindi"]`).
- `accent` (string, optional) — Accent (e.g. `american`, `british`, `indian`).
- `gender` (string, optional) — Gender label (`male` or `female`).
- `age` (string, optional) — Age range (e.g. `young`, `middle aged`, `senior`).
- `emotions` (list of string, optional) — Emotional ranges the voice supports. May be empty.
- `usecases` (list of string, optional) — Recommended use cases (e.g. `conversational`, `narration`).

## Examples

### Lightning v3.1 Standard pool (sample)

**Response**

```json
{
  "voices": [
    {
      "voiceId": "avery",
      "displayName": "Avery",
      "tags": {
        "language": [
          "english"
        ],
        "accent": "american",
        "gender": "female",
        "age": "young",
        "emotions": [],
        "usecases": [
          "conversational"
        ]
      }
    },
    {
      "voiceId": "liam",
      "displayName": "Liam",
      "tags": {
        "language": [
          "english"
        ],
        "accent": "british",
        "gender": "male",
        "age": "young",
        "emotions": [],
        "usecases": [
          "conversational"
        ]
      }
    },
    {
      "voiceId": "devansh",
      "displayName": "Devansh",
      "tags": {
        "language": [
          "hindi",
          "english"
        ],
        "accent": "indian",
        "gender": "male",
        "age": "young",
        "emotions": [],
        "usecases": [
          "conversational"
        ]
      }
    },
    {
      "voiceId": "mishka",
      "displayName": "Mishka",
      "tags": {
        "language": [
          "hindi",
          "english",
          "marathi",
          "gujarati",
          "punjabi",
          "bengali",
          "odia",
          "tamil",
          "telugu"
        ],
        "accent": "indian",
        "gender": "female",
        "age": "young",
        "emotions": [],
        "usecases": [
          "conversational"
        ]
      }
    }
  ]
}
```

**SDK Code**

```python Lightning v3.1 Standard pool (sample)
import requests

url = "https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices"

response = requests.get(url)

print(response.json())
```

```javascript Lightning v3.1 Standard pool (sample)
const url = 'https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices';
const options = {method: 'GET'};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Lightning v3.1 Standard pool (sample)
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices"

	req, _ := http.NewRequest("GET", url, nil)

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Lightning v3.1 Standard pool (sample)
require 'uri'
require 'net/http'

url = URI("https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)

response = http.request(request)
puts response.read_body
```

```java Lightning v3.1 Standard pool (sample)
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse<String> response = Unirest.get("https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices")
  .asString();
```

```php Lightning v3.1 Standard pool (sample)
<?php
require_once('vendor/autoload.php');

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices');

echo $response->getBody();
```

```csharp Lightning v3.1 Standard pool (sample)
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices");
var request = new RestRequest(Method.GET);
IRestResponse response = client.Execute(request);
```

```swift Lightning v3.1 Standard pool (sample)
import Foundation

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"

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

### Lightning v3.1 Pro pool (sample)

**Response**

```json
{
  "voices": [
    {
      "voiceId": "meher",
      "displayName": "Meher",
      "tags": {
        "language": [
          "hindi",
          "english"
        ],
        "accent": "indian",
        "gender": "female",
        "age": "young",
        "emotions": [],
        "usecases": [
          "conversational"
        ]
      }
    },
    {
      "voiceId": "raghav",
      "displayName": "Raghav",
      "tags": {
        "language": [
          "hindi",
          "english"
        ],
        "accent": "indian",
        "gender": "male",
        "age": "middle aged",
        "emotions": [],
        "usecases": [
          "conversational",
          "narration"
        ]
      }
    }
  ]
}
```

**SDK Code**

```python Lightning v3.1 Pro pool (sample)
import requests

url = "https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices"

response = requests.get(url)

print(response.json())
```

```javascript Lightning v3.1 Pro pool (sample)
const url = 'https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices';
const options = {method: 'GET'};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

```go Lightning v3.1 Pro pool (sample)
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices"

	req, _ := http.NewRequest("GET", url, nil)

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby Lightning v3.1 Pro pool (sample)
require 'uri'
require 'net/http'

url = URI("https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)

response = http.request(request)
puts response.read_body
```

```java Lightning v3.1 Pro pool (sample)
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse<String> response = Unirest.get("https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices")
  .asString();
```

```php Lightning v3.1 Pro pool (sample)
<?php
require_once('vendor/autoload.php');

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices');

echo $response->getBody();
```

```csharp Lightning v3.1 Pro pool (sample)
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices");
var request = new RestRequest(Method.GET);
IRestResponse response = client.Execute(request);
```

```swift Lightning v3.1 Pro pool (sample)
import Foundation

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/lightning-v3.1/get_voices")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"

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