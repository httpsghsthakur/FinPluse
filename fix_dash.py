import re

with open(r'src\pages\DashboardPage.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add ShareInsightModal import
old_import = "from \"../components/ui/ChartCard\";"
new_import = '''from "../components/ui/ChartCard";
import { ShareInsightModal } from "../components/ui/ShareInsightModal";'''
text = text.replace(old_import, new_import)

# 2. Add state for the modal
old_state = "const { data, loading, error } = useDashboardData();"
new_state = '''const { data, loading, error } = useDashboardData();
  const [shareOpen, setShareOpen] = React.useState(false);'''
text = text.replace(old_state, new_state)

# 3. Add Share button to the header
old_header = '''        <h1 className="text-2xl font-medium tracking-tight text-white">
          Overview
        </h1>'''
new_header = '''        <div className="flex items-center justify-between w-full">
          <h1 className="text-2xl font-medium tracking-tight text-white">
            Overview
          </h1>
          <button 
            onClick={() => setShareOpen(true)}
            className="flex items-center gap-2 bg-[#141414] hover:bg-[#1a1a1a] border border-white/[0.08] px-4 py-2 rounded-lg text-sm text-white transition-colors"
          >
            <Share2 className="w-4 h-4" />
            Share Milestone
          </button>
        </div>'''
text = text.replace(old_header, new_header)

# 4. Add the modal at the end of the return statement
old_return = '''    </div>
  );
};'''
new_return = '''      <ShareInsightModal 
        isOpen={shareOpen} 
        onClose={() => setShareOpen(false)} 
        title="Financial Milestone Achieved!" 
        insight={I've maintained a positive cash flow with a liquid balance of  this month using Finpluse's AI forecasting!}
      />
    </div>
  );
};'''
text = text.replace(old_return, new_return)

with open(r'src\pages\DashboardPage.tsx', 'w', encoding='utf-8') as f:
    f.write(text)
