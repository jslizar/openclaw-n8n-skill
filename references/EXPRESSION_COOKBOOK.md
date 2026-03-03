# n8n Expression Cookbook

80+ copy-paste-ready expressions. Use these instead of composing from scratch.

All expressions go inside `{{ }}` in node parameters. NEVER use `{{ }}` inside Code nodes.

---

## Data Access

```javascript
// Current item
{{ $json.fieldName }}
{{ $json.nested.field }}
{{ $json.body.email }}                    // Webhook POST body
{{ $json.headers.authorization }}         // Webhook headers (lowercase!)
{{ $json.query.page }}                    // Webhook query params

// From specific node
{{ $('Node Name').item.json.field }}
{{ $('Webhook').item.json.body.email }}

// First/last item
{{ $input.first().json.field }}
{{ $input.last().json.field }}

// Item count
{{ $input.all().length }}

// By index
{{ $input.all()[0].json.field }}
{{ $input.all()[2].json.name }}
```

---

## Null Safety & Defaults

```javascript
// Fallback value
{{ $json.name || 'Unknown' }}
{{ $json.email || 'no-email@placeholder.com' }}

// Optional chaining (prevents "cannot read undefined")
{{ $json.body?.email }}
{{ $json.data?.results?.[0]?.name }}
{{ $json.user?.address?.city ?? 'Not provided' }}

// Nullish coalescing (only catches null/undefined, not empty string)
{{ $json.count ?? 0 }}
{{ $json.name ?? 'N/A' }}

// Check if field exists
{{ $json.email ? 'Has email' : 'No email' }}
{{ $json.items?.length > 0 ? 'Has items' : 'Empty' }}

// Default for empty string specifically
{{ $json.name || $json.username || 'Anonymous' }}
```

---

## String Operations

```javascript
// Template literals
{{ `Hello ${$json.firstName} ${$json.lastName}` }}
{{ `Order #${$json.orderId} is ${$json.status}` }}
{{ `${$json.city}, ${$json.state} ${$json.zip}` }}

// Case conversion
{{ $json.name.toUpperCase() }}
{{ $json.name.toLowerCase() }}
{{ $json.name.charAt(0).toUpperCase() + $json.name.slice(1) }}   // Capitalize first

// Trim & clean
{{ $json.input.trim() }}
{{ $json.text.replace(/\s+/g, ' ').trim() }}                     // Collapse whitespace

// Substring
{{ $json.description.substring(0, 100) }}                         // First 100 chars
{{ $json.description.slice(0, 100) + ($json.description.length > 100 ? '...' : '') }}

// Split & join
{{ $json.fullName.split(' ')[0] }}                                // First name
{{ $json.fullName.split(' ').slice(1).join(' ') }}                // Last name(s)
{{ $json.tags.join(', ') }}                                       // Array to comma string
{{ $json.csv.split(',').map(s => s.trim()) }}                     // CSV to array

// Replace
{{ $json.phone.replace(/[^0-9]/g, '') }}                          // Strip non-digits
{{ $json.text.replace(/\n/g, '<br>') }}                           // Newlines to HTML
{{ $json.url.replace('http://', 'https://') }}                    // Force HTTPS

// Contains / includes
{{ $json.email.includes('@gmail.com') ? 'Gmail' : 'Other' }}
{{ $json.tags.includes('urgent') ? '🔴' : '🟢' }}

// Email domain extraction
{{ $json.email.split('@')[1] }}
{{ $json.email.split('@')[0] }}                                   // Username part

// URL encoding
{{ encodeURIComponent($json.searchQuery) }}
{{ decodeURIComponent($json.encodedParam) }}
```

---

## Number Operations

```javascript
// Rounding
{{ Math.round($json.price * 100) / 100 }}                        // 2 decimal places
{{ $json.price.toFixed(2) }}                                      // "19.99" (string)
{{ Math.ceil($json.items / 10) }}                                 // Round up
{{ Math.floor($json.score) }}                                     // Round down

// Currency formatting
{{ '$' + $json.amount.toFixed(2) }}                               // $19.99
{{ ($json.amount / 100).toFixed(2) }}                             // Cents to dollars

// Percentage
{{ Math.round($json.completed / $json.total * 100) }}            // 75
{{ (($json.completed / $json.total) * 100).toFixed(1) + '%' }}   // 75.0%

// Min / Max / Clamp
{{ Math.min($json.value, 100) }}                                  // Cap at 100
{{ Math.max($json.value, 0) }}                                    // Floor at 0
{{ Math.min(Math.max($json.value, 0), 100) }}                    // Clamp 0-100

// Random
{{ Math.random().toString(36).substring(2, 10) }}                 // Random 8-char string
{{ Math.floor(Math.random() * 1000) }}                            // Random number 0-999

// Parse numbers from strings
{{ parseInt($json.quantity, 10) }}
{{ parseFloat($json.price) }}
{{ Number($json.stringValue) || 0 }}                              // Safe parse with default
```

---

## Date & Time (Luxon)

```javascript
// Current time
{{ $now.toISO() }}                                                // 2026-02-27T14:30:00.000Z
{{ $now.toFormat('yyyy-MM-dd') }}                                 // 2026-02-27
{{ $now.toFormat('yyyy-MM-dd HH:mm:ss') }}                       // 2026-02-27 14:30:00
{{ $now.toFormat('MM/dd/yyyy') }}                                 // 02/27/2026
{{ $now.toFormat('MMMM d, yyyy') }}                               // February 27, 2026
{{ $now.toFormat('EEE, MMM d') }}                                 // Thu, Feb 27
{{ $now.toFormat('HH:mm') }}                                      // 14:30
{{ $now.toMillis() }}                                             // Unix ms timestamp
{{ Math.floor($now.toMillis() / 1000) }}                          // Unix seconds

// Date math
{{ $now.minus({ days: 1 }).toISO() }}                             // Yesterday
{{ $now.minus({ days: 7 }).toFormat('yyyy-MM-dd') }}              // 7 days ago
{{ $now.plus({ hours: 24 }).toISO() }}                            // Tomorrow
{{ $now.plus({ months: 1 }).toFormat('yyyy-MM-dd') }}             // Next month
{{ $now.startOf('day').toISO() }}                                 // Start of today
{{ $now.endOf('day').toISO() }}                                   // End of today
{{ $now.startOf('month').toFormat('yyyy-MM-dd') }}                // First of month
{{ $now.endOf('month').toFormat('yyyy-MM-dd') }}                  // Last of month
{{ $now.startOf('week').toFormat('yyyy-MM-dd') }}                 // Monday of this week

// Parse dates
{{ DateTime.fromISO($json.date).toFormat('MM/dd/yyyy') }}
{{ DateTime.fromISO($json.date).toFormat('yyyy-MM-dd') }}
{{ DateTime.fromFormat($json.date, 'MM/dd/yyyy').toISO() }}
{{ DateTime.fromMillis($json.timestamp).toISO() }}
{{ DateTime.fromSeconds($json.unixTimestamp).toISO() }}

// Compare dates
{{ DateTime.fromISO($json.dueDate) < $now ? 'Overdue' : 'On time' }}
{{ DateTime.fromISO($json.createdAt).diff($now, 'days').days }}   // Days between
{{ Math.abs(DateTime.fromISO($json.date).diff($now, 'hours').hours) }}  // Hours between

// Timezone conversion
{{ $now.setZone('America/New_York').toFormat('HH:mm z') }}
{{ $now.setZone('Europe/London').toISO() }}
{{ DateTime.fromISO($json.date).setZone('America/Los_Angeles').toFormat('yyyy-MM-dd HH:mm') }}

// Relative time
{{ DateTime.fromISO($json.createdAt).toRelative() }}              // "2 hours ago"

// Date parts
{{ $now.year }}                                                    // 2026
{{ $now.month }}                                                   // 2 (February)
{{ $now.day }}                                                     // 27
{{ $now.weekday }}                                                 // 4 (Thursday, 1=Mon)
{{ $now.hour }}
{{ $now.minute }}
```

---

## Array Operations

```javascript
// Length
{{ $json.items.length }}
{{ $json.results?.length ?? 0 }}

// Map (transform each item)
{{ $json.users.map(u => u.name) }}                                // Extract names
{{ $json.users.map(u => u.email).join(', ') }}                    // Emails as string
{{ $json.items.map(i => i.price).reduce((a, b) => a + b, 0) }}   // Sum prices

// Filter
{{ $json.items.filter(i => i.active) }}                           // Active only
{{ $json.items.filter(i => i.status === 'open') }}
{{ $json.items.filter(i => i.amount > 100) }}
{{ $json.items.filter(i => i.email?.includes('@')) }}              // Has valid-ish email

// Find single item
{{ $json.items.find(i => i.id === $json.targetId) }}
{{ $json.items.find(i => i.primary === true)?.email }}

// Sort
{{ $json.items.sort((a, b) => a.name.localeCompare(b.name)) }}    // Alpha sort
{{ $json.items.sort((a, b) => b.score - a.score) }}               // Numeric desc

// Slice
{{ $json.items.slice(0, 10) }}                                    // First 10
{{ $json.items.slice(-5) }}                                       // Last 5

// Unique values
{{ [...new Set($json.items.map(i => i.category))] }}

// Check contents
{{ $json.tags.includes('vip') }}                                  // true/false
{{ $json.items.some(i => i.status === 'error') }}                 // Any errors?
{{ $json.items.every(i => i.valid) }}                             // All valid?

// Flatten
{{ $json.nestedArrays.flat() }}                                   // One level
{{ $json.deepNested.flat(Infinity) }}                             // All levels
```

---

## JSON Operations

```javascript
// Stringify
{{ JSON.stringify($json.data) }}
{{ JSON.stringify($json.data, null, 2) }}                         // Pretty print
{{ JSON.stringify({ name: $json.name, email: $json.email }) }}    // Build object

// Parse
{{ JSON.parse($json.jsonString) }}
{{ JSON.parse($json.rawBody).data }}

// Object keys / values
{{ Object.keys($json.data) }}                                     // ["key1", "key2"]
{{ Object.values($json.data) }}                                   // [val1, val2]
{{ Object.entries($json.data).length }}                           // Number of fields

// Merge objects
{{ {...$json.defaults, ...$json.overrides} }}

// Pick specific fields
{{ JSON.stringify({ id: $json.id, name: $json.name }) }}

// Remove a field (spread rest)
{{ (() => { const {password, ...rest} = $json; return JSON.stringify(rest); })() }}
```

---

## Conditional / Logic

```javascript
// Ternary
{{ $json.status === 'active' ? '✅ Active' : '❌ Inactive' }}
{{ $json.score >= 90 ? 'A' : $json.score >= 80 ? 'B' : $json.score >= 70 ? 'C' : 'F' }}

// Boolean coercion
{{ !!$json.email }}                                               // true if exists and non-empty
{{ !$json.deleted }}                                              // true if not deleted

// Type checking
{{ typeof $json.value === 'string' ? $json.value : String($json.value) }}
{{ Array.isArray($json.tags) ? $json.tags.join(', ') : $json.tags }}

// Multiple conditions
{{ ($json.role === 'admin' || $json.role === 'owner') ? 'Full access' : 'Limited' }}
{{ ($json.verified && $json.active) ? 'Ready' : 'Pending' }}
```

---

## Workflow & Execution Context

```javascript
// Execution info
{{ $execution.id }}                                               // Current execution ID
{{ $execution.mode }}                                             // "manual" or "trigger"
{{ $execution.resumeUrl }}                                        // For Wait node resume

// Workflow info
{{ $workflow.id }}                                                // Workflow ID
{{ $workflow.name }}                                              // Workflow name
{{ $workflow.active }}                                            // true/false

// Environment variables
{{ $env.API_BASE_URL }}
{{ $env.SLACK_CHANNEL }}
{{ $env.DATABASE_HOST }}

// Loop context
{{ $runIndex }}                                                   // Current loop iteration (0-based)
{{ $itemIndex }}                                                  // Current item index

// Previous node
{{ $prevNode.name }}                                              // Name of previous node
{{ $prevNode.outputIndex }}                                       // Which output (0 = first/true)

// Build dynamic URLs
{{ `${$env.API_BASE_URL}/users/${$json.userId}` }}
{{ `https://app.example.com/orders/${$json.orderId}` }}
```

---

## Slack Formatting

```javascript
// Bold, italic, code
{{ `*${$json.title}*` }}                                          // Bold
{{ `_${$json.note}_` }}                                           // Italic
{{ `\`${$json.code}\`` }}                                         // Inline code
{{ `\`\`\`${$json.codeBlock}\`\`\`` }}                           // Code block

// Links
{{ `<${$json.url}|Click here>` }}
{{ `<mailto:${$json.email}|${$json.name}>` }}

// User mention
{{ `<@${$json.slackUserId}>` }}

// Channel link
{{ `<#${$json.channelId}>` }}

// Multi-line message
{{ `🔔 *New Lead*\n*Name:* ${$json.name}\n*Email:* ${$json.email}\n*Company:* ${$json.company || 'N/A'}\n*Source:* ${$json.source}` }}
```

---

## Email / HTML Formatting

```javascript
// HTML paragraph
{{ `<p>${$json.message}</p>` }}

// HTML table row
{{ `<tr><td>${$json.name}</td><td>${$json.email}</td><td>${$json.status}</td></tr>` }}

// Link
{{ `<a href="${$json.url}">${$json.linkText}</a>` }}

// Line breaks (plain text email)
{{ $json.items.map(i => `- ${i.name}: $${i.price}`).join('\n') }}
```

---

## Common Patterns

```javascript
// Generate unique ID
{{ `${$workflow.id}-${$execution.id}-${$itemIndex}` }}
{{ Date.now().toString(36) + Math.random().toString(36).slice(2, 7) }}

// Webhook path from workflow ID (always unique)
={{ $workflow.id }}

// Hash for deduplication
{{ $json.email.toLowerCase().trim() }}

// Safe number from string
{{ Number($json.value) || 0 }}
{{ parseInt($json.quantity, 10) || 1 }}

// Boolean from various formats
{{ $json.active === true || $json.active === 'true' || $json.active === 1 || $json.active === '1' }}

// Truncate with ellipsis
{{ $json.text.length > 200 ? $json.text.slice(0, 197) + '...' : $json.text }}

// Capitalize each word
{{ $json.name.replace(/\b\w/g, c => c.toUpperCase()) }}

// Sanitize for filename
{{ $json.title.replace(/[^a-zA-Z0-9-_]/g, '_').toLowerCase() }}

// Build query string
{{ Object.entries($json.params).map(([k,v]) => `${k}=${encodeURIComponent(v)}`).join('&') }}
```
