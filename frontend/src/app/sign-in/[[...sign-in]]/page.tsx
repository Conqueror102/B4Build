import { SignIn } from "@clerk/nextjs";

export const metadata = { title: "Sign in" };

export default function SignInPage() {
  return (
    <div className="grid min-h-[80vh] place-items-center px-4">
      <div className="rounded-2xl gradient-bg p-px glow">
        <div className="rounded-[15px] bg-background p-2">
          <SignIn />
        </div>
      </div>
    </div>
  );
}
