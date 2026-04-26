import { SignUp } from "@clerk/nextjs";

export const metadata = { title: "Sign up" };

export default function SignUpPage() {
  return (
    <div className="grid min-h-[80vh] place-items-center px-4">
      <div className="rounded-2xl gradient-bg p-px glow">
        <div className="rounded-[15px] bg-background p-2">
          <SignUp />
        </div>
      </div>
    </div>
  );
}
