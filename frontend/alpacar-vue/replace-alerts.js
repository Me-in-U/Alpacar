import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Files to process (from grep results)
const filesToProcess = [
  'src/components/Header.vue',
  'src/views/user/ForgotPassword.vue',
  'src/views/user/GoogleCallback.vue',
  'src/views/user/Login.vue',
  'src/views/admin/AdminLogin.vue',
  'src/views/admin/AdminMain.vue',
  'src/views/admin/AdminParkingLogs.vue',
  'src/views/user/Signup.vue',
  'src/views/user/SocialLoginInfo.vue',
  'src/views/user/UserProfile.vue',
  'src/views/user/UserSetting.vue'
];

// Alert replacement patterns
const replacements = [
  {
    pattern: /(\s+)alert\s*\(\s*"([^"]+)"\s*\)\s*;/g,
    replacement: '$1await alert("$2");'
  },
  {
    pattern: /(\s+)alert\s*\(\s*`([^`]+)`\s*\)\s*;/g,
    replacement: '$1await alert(`$2`);'
  },
  {
    pattern: /(\s+)alert\s*\(\s*([^"`;]+)\s*\)\s*;/g,
    replacement: '$1await alert($2);'
  },
  {
    pattern: /return\s+alert\s*\(\s*"([^"]+)"\s*\)\s*;/g,
    replacement: 'await alert("$1"); return;'
  },
  {
    pattern: /return\s+alert\s*\(\s*`([^`]+)`\s*\)\s*;/g,
    replacement: 'await alert(`$1`); return;'
  },
  {
    pattern: /return\s+alert\s*\(\s*([^"`;]+)\s*\)\s*;/g,
    replacement: 'await alert($1); return;'
  },
  {
    pattern: /if\s*\([^)]+\)\s*return\s+alert\s*\(\s*"([^"]+)"\s*\)\s*;/g,
    replacement: (match, condition, message) => match.replace(/return\s+alert\s*\(\s*"([^"]+)"\s*\)/, 'await alert("$1"); return')
  }
];

// Import statement to add
const importStatement = `import { alert, alertSuccess, alertWarning, alertError, confirm } from "@/composables/useAlert";`;

function processFile(filePath) {
  const fullPath = path.join(__dirname, filePath);
  
  if (!fs.existsSync(fullPath)) {
    console.log(`File not found: ${fullPath}`);
    return;
  }
  
  let content = fs.readFileSync(fullPath, 'utf8');
  let hasChanges = false;
  
  // Check if file contains alert() calls
  if (!content.includes('alert(')) {
    console.log(`No alerts found in ${filePath}`);
    return;
  }
  
  // Add import if not present
  if (!content.includes('@/composables/useAlert')) {
    // Find the imports section
    const scriptMatch = content.match(/<script[^>]*>/);
    if (scriptMatch) {
      const importMatch = content.match(/import[^;]+from[^;]+;/g);
      if (importMatch) {
        const lastImport = importMatch[importMatch.length - 1];
        const lastImportIndex = content.indexOf(lastImport) + lastImport.length;
        content = content.slice(0, lastImportIndex) + '\n' + importStatement + content.slice(lastImportIndex);
        hasChanges = true;
      }
    }
  }
  
  // Apply replacements
  for (const { pattern, replacement } of replacements) {
    const newContent = content.replace(pattern, replacement);
    if (newContent !== content) {
      content = newContent;
      hasChanges = true;
    }
  }
  
  // Write back if changed
  if (hasChanges) {
    fs.writeFileSync(fullPath, content, 'utf8');
    console.log(`✅ Updated ${filePath}`);
  } else {
    console.log(`⚪ No changes needed for ${filePath}`);
  }
}

// Process all files
console.log('🔄 Starting alert replacement...\n');

filesToProcess.forEach(filePath => {
  try {
    processFile(filePath);
  } catch (error) {
    console.error(`❌ Error processing ${filePath}:`, error.message);
  }
});

console.log('\n✅ Alert replacement completed!');