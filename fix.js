const fs = require('fs'); let c = fs.readFileSync('src/lib/supabase.ts', 'utf8'); c = c.replace('\\\\Bearer \\\\', '\Bearer \\'); fs.writeFileSync('src/lib/supabase.ts', c);
