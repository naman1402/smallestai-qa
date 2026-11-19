> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 Pro (current TTS) and Pulse (current
> multilingual STT) — or Pulse 2.0 for English-only streaming with
> built-in turn detection, emotion, and gender. Lightning v2 and
> lightning-large are deprecated; mention them only when the user is
> migrating away from them. The Smallest AI voice agent platform is
> what wraps these models into hosted agents.

# Create a Voice Clone

POST https://api.smallest.ai/waves/v1/voice-cloning
Content-Type: multipart/form-data

Create an instant voice clone in a single call. Defaults to `lightning-v3.1`.


Reference: https://docs.smallest.ai/api-reference/models/text-to-speech/create-voice-clone

## Authentication

- `Authorization` header (required) (prefixed with ` Bearer  `) — API key authentication. Include your key as `Authorization: Bearer YOUR_API_KEY`. `POST /waves/v1/stt`, the text-to-speech endpoints and the speech WebSockets also accept short-lived access tokens; other endpoints need an API key. See [Token-based authentication](/api-reference/token-based-authentication).

## Request

### Body (multipart/form-data)

This endpoint expects a multipart form containing a file.

- `displayName` (string, required) — Human-readable name for the voice clone.
- `file` (file, required) — Audio file to clone from. Supported MIME types: `audio/mpeg`, `audio/mpeg-3`, `audio/wav`, `audio/wave`, `audio/webm`, `video/webm`, `audio/mp4`, `video/mp4`. Maximum size: 5 MB.
- `description` (string, optional) — Optional longer description for the voice clone.
- `accent` (string, optional) — Optional accent tag (e.g. "general", "indian").
- `tags` (string, optional) — Optional comma-separated list of tags. Server splits on commas and trims whitespace (`"en, tone-test"` → `["en", "tone-test"]`).
- `language` (enum, optional) — Primary language the clone will be used for. Optional, but **strongly recommended** — set it to the language of your reference audio. The TTS request's `language` should also match this code; setting it now avoids silent language mismatches at inference time. Must be one of the languages supported by `lightning-v3.1`. The server validates and rejects unsupported codes with a 400.
- `model` (enum, optional) — Voice cloning model. Defaults to `lightning-v3.1`. Pass `lightning-v3.1-pro` to clone onto the premium Pro pool. `lightning-v2` is accepted by the schema for historical reasons but is deprecated - the server returns 400 with `"Voice cloning for lightning-v2 is deprecated. Please use lightning-v3.1"`.

## Response

### 200

Voice clone created. Includes pre-generated sample clips of the new voice.

- `message` (string, optional)
- `data` (WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaData, optional)

## Errors

### 400 Bad Request Error

Validation error. Common causes: no file provided, invalid MIME type, file too large, clone limit exceeded, invalid language, or `model=lightning-v2` (deprecated).

- `error` (string, optional) — Error message.

### 401 Unauthorized Error

Unauthorized — missing or invalid API key.

- `error` (string, optional)

### 500 Internal Server Error

Server error. The `error_code` field may be populated for known failure modes.

- `error` (string, optional)
- `error_code` (enum, optional) — Present when a known failure mode occurred.
  - Allowed values: `voice_clone_timeout`, `voice_clone_error`

## Types

### WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaData

- `voiceId` (string, optional) — Unique voice ID. Pass this as `voice_id` in TTS requests.
- `displayName` (string, optional)
- `model` (string, optional) — Internal model document for the cloned voice.
- `status` (enum, optional)
  - Allowed values: `pending`, `processing`, `completed`, `failed`
- `language` (string, optional)
- `audioFileNames` (list of string, optional)
- `createdAt` (datetime, optional)
- `organizationId` (string, optional)
- `samples` (list of WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaDataSamplesItems, optional) — Pre-generated sample audio clips in the cloned voice.

### WavesV1VoiceCloningPostResponsesContentApplicationJsonSchemaDataSamplesItems

- `text` (string, optional) — Text that was synthesized.
- `audioUrl` (string, optional) — Signed URL to the generated sample audio.

## Examples

**Request**

```json
{
  "accent": {
    "type": "json"
  },
  "description": {
    "type": "json"
  },
  "displayName": {
    "type": "json",
    "value": "my-custom-voice"
  },
  "file": "<file: [object Object]>",
  "language": {
    "type": "json"
  },
  "model": {
    "type": "json"
  },
  "tags": {
    "type": "json"
  }
}
```

**Response**

```json
{
  "message": "Voice clone created successfully",
  "data": {
    "voiceId": "voice_dLP5T67Qw7",
    "displayName": "string",
    "model": "string",
    "status": "pending",
    "language": "string",
    "audioFileNames": [
      "string"
    ],
    "createdAt": "2024-01-15T09:30:00Z",
    "organizationId": "string",
    "samples": [
      {
        "text": "string",
        "audioUrl": "string"
      }
    ]
  }
}
```

**SDK Code**

```python
import requests

url = "https://api.smallest.ai/waves/v1/voice-cloning"

files = { "file": "open('[object Object]', 'rb')" }
payload = {
    "accent": "{
  \"type\": \"json\"
}",
    "description": "{
  \"type\": \"json\"
}",
    "displayName": "{
  \"type\": \"json\",
  \"value\": \"my-custom-voice\"
}",
    "language": "{
  \"type\": \"json\"
}",
    "model": "{
  \"type\": \"json\"
}",
    "tags": "{
  \"type\": \"json\"
}"
}
headers = {"Authorization": "Bearer <BearerAuth>"}

response = requests.post(url, data=payload, files=files, headers=headers)

print(response.json())
```

```javascript
const url = 'https://api.smallest.ai/waves/v1/voice-cloning';
const form = new FormData();
form.append('accent', '{
  "type": "json"
}');
form.append('description', '{
  "type": "json"
}');
form.append('displayName', '{
  "type": "json",
  "value": "my-custom-voice"
}');
form.append('file', '[object Object]');
form.append('language', '{
  "type": "json"
}');
form.append('model', '{
  "type": "json"
}');
form.append('tags', '{
  "type": "json"
}');

const options = {method: 'POST', headers: {Authorization: 'Bearer <BearerAuth>'}};

options.body = form;

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

	url := "https://api.smallest.ai/waves/v1/voice-cloning"

	payload := strings.NewReader("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"accent\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"displayName\"\r\n\r\n{\n  \"type\": \"json\",\n  \"value\": \"my-custom-voice\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"[object Object]\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"language\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"tags\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001--\r\n")

	req, _ := http.NewRequest("POST", url, payload)

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

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer <BearerAuth>'
request.body = "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"accent\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"displayName\"\r\n\r\n{\n  \"type\": \"json\",\n  \"value\": \"my-custom-voice\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"[object Object]\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"language\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"tags\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001--\r\n"

response = http.request(request)
puts response.read_body
```

```java
import com.mashape.unirest.http.HttpResponse;
import com.mashape.unirest.http.Unirest;

HttpResponse<String> response = Unirest.post("https://api.smallest.ai/waves/v1/voice-cloning")
  .header("Authorization", "Bearer <BearerAuth>")
  .body("-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"accent\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"displayName\"\r\n\r\n{\n  \"type\": \"json\",\n  \"value\": \"my-custom-voice\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"[object Object]\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"language\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"tags\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001--\r\n")
  .asString();
```

```php
<?php
require_once('vendor/autoload.php');

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.smallest.ai/waves/v1/voice-cloning', [
  'multipart' => [
    [
        'name' => 'accent',
        'contents' => '{
  "type": "json"
}'
    ],
    [
        'name' => 'description',
        'contents' => '{
  "type": "json"
}'
    ],
    [
        'name' => 'displayName',
        'contents' => '{
  "type": "json",
  "value": "my-custom-voice"
}'
    ],
    [
        'name' => 'file',
        'filename' => '[object Object]',
        'contents' => null
    ],
    [
        'name' => 'language',
        'contents' => '{
  "type": "json"
}'
    ],
    [
        'name' => 'model',
        'contents' => '{
  "type": "json"
}'
    ],
    [
        'name' => 'tags',
        'contents' => '{
  "type": "json"
}'
    ]
  ]
  'headers' => [
    'Authorization' => 'Bearer <BearerAuth>',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.smallest.ai/waves/v1/voice-cloning");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer <BearerAuth>");
request.AddParameter("undefined", "-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"accent\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"displayName\"\r\n\r\n{\n  \"type\": \"json\",\n  \"value\": \"my-custom-voice\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"file\"; filename=\"[object Object]\"\r\nContent-Type: application/octet-stream\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"language\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"tags\"\r\n\r\n{\n  \"type\": \"json\"\n}\r\n-----011000010111000001101001--\r\n", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = ["Authorization": "Bearer <BearerAuth>"]
let parameters = [
  [
    "name": "accent",
    "value": "{
  \"type\": \"json\"
}"
  ],
  [
    "name": "description",
    "value": "{
  \"type\": \"json\"
}"
  ],
  [
    "name": "displayName",
    "value": "{
  \"type\": \"json\",
  \"value\": \"my-custom-voice\"
}"
  ],
  [
    "name": "file",
    "fileName": "[object Object]"
  ],
  [
    "name": "language",
    "value": "{
  \"type\": \"json\"
}"
  ],
  [
    "name": "model",
    "value": "{
  \"type\": \"json\"
}"
  ],
  [
    "name": "tags",
    "value": "{
  \"type\": \"json\"
}"
  ]
]

let boundary = "---011000010111000001101001"

var body = ""
var error: NSError? = nil
for param in parameters {
  let paramName = param["name"]!
  body += "--\(boundary)\r\n"
  body += "Content-Disposition:form-data; name=\"\(paramName)\""
  if let filename = param["fileName"] {
    let contentType = param["content-type"]!
    let fileContent = String(contentsOfFile: filename, encoding: String.Encoding.utf8)
    if (error != nil) {
      print(error as Any)
    }
    body += "; filename=\"\(filename)\"\r\n"
    body += "Content-Type: \(contentType)\r\n\r\n"
    body += fileContent
  } else if let paramValue = param["value"] {
    body += "\r\n\r\n\(paramValue)"
  }
}

let request = NSMutableURLRequest(url: NSURL(string: "https://api.smallest.ai/waves/v1/voice-cloning")! as URL,
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