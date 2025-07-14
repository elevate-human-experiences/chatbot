import { User } from "lucide-react";

interface UserInfoProps {
  user: {
    id: string;
    name: string;
    email: string;
  } | null;
}

export function UserInfo({ user }: UserInfoProps) {
  return (
    <div className="p-4 border-b border-gray-700 z-0 bg-gray-800">
      <div className="flex items-center space-x-3 p-3 rounded-lg bg-gray-800">
        <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
          <User className="w-4 h-4 text-white" />
        </div>
        <div>
          {user ? (
            <>
              <div className="font-medium text-sm text-white truncate">{user.name}</div>
              <div className="text-xs text-gray-400 truncate">{user.email}</div>
            </>
          ) : (
            <div className="text-xs text-gray-400">No user logged in</div>
          )}
        </div>
      </div>
    </div>
  );
}
