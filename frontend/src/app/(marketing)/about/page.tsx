import { GradientHeading } from "@/components/brand/gradient-heading";

export const metadata = {
  title: "About | AI Build Advisor",
  description: "The story behind the AI Build Advisor.",
};

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-24 sm:px-6 lg:px-8">
      <GradientHeading as="h1" className="text-left mb-8">
        Why build an AI advisor?
      </GradientHeading>

      <div className="prose prose-invert prose-p:leading-relaxed prose-p:text-muted-foreground prose-a:text-primary hover:prose-a:text-primary/80 prose-headings:text-foreground">
        <p className="text-lg">
          Building software is hard. Building AI software right now feels like standing in a hurricane of new models, frameworks, and conflicting opinions. 
        </p>

        <p>
          Too often, developers jump straight into coding an AI idea without stopping to pressure-test the underlying assumptions. We pick a vector database because we saw it on Twitter. We string together LLM calls without calculating the token costs at scale. We build complex RAG pipelines for problems that could be solved with a simple BM25 search.
        </p>

        <h2>The Cost of Skipping Architecture</h2>
        
        <p>
          I built the <strong>AI Build Advisor</strong> because I've made all these mistakes. I've deployed applications that cost $400/month in OpenAI API fees because I didn't do the math on active users vs token counts. I've spent weeks building custom auth when Clerk or Supabase would have sufficed.
        </p>
        
        <p>
          What I needed was a ruthless, experienced Staff Engineer sitting next to me—someone who would ask annoying questions like: <em>"Why are you using a graph database for this?"</em> and <em>"What happens when the LLM hallucinates a SQL injection?"</em>
        </p>

        <h2>Enter the Agentic Workflow</h2>

        <p>
          The AI Build Advisor is built on a <strong>multi-agent LangGraph architecture</strong>. It doesn't just spit out a generic block of text. It forces you to answer clarifying questions. It breaks down the problem into 9 distinct phases. And crucially, it employs an <em>Adversarial Red Team</em> agent whose sole job is to tear your architecture apart and find the holes before you write a single line of code.
        </p>

        <p>
          My hope is that this tool saves you weeks of wasted engineering effort and thousands of dollars in regret.
        </p>

        <div className="mt-12 p-6 rounded-2xl border border-border/40 bg-muted/20">
          <p className="m-0 text-sm">
            <strong>About the Author:</strong> This project is a portfolio showcase. The code is entirely open-source and built to demonstrate advanced agentic workflows, deterministic diffing, and modern React frontend patterns.
          </p>
        </div>
      </div>
    </div>
  );
}
