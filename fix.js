const fs = require('fs'); let c = fs.readFileSync('src/pages/LandingPage.tsx', 'utf8'); c = c.replace(/"$/, ''); fs.writeFileSync('src/pages/LandingPage.tsx', c);
