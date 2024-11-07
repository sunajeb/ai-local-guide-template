"use client";

import Link from "next/link";
import Logo from "./logo";

export default function Header() {
  return (
    <header className="z-30 mt-2 w-full md:mt-5">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
        {/* <div className="relative flex h-14 items-center justify-between gap-3 rounded-2xl px-3 before:pointer-events-none before:absolute before:inset-0 before:rounded-[inherit] before:[background:linear-gradient(to_right,theme(colors.gray.800),theme(colors.gray.700),theme(colors.gray.800))_border-box] before:[mask-composite:exclude_!important] before:[mask:linear-gradient(white_0_0)_padding-box,_linear-gradient(white_0_0)] after:absolute after:inset-0 after:-z-10 after:backdrop-blur-sm">
          
          <div className="flex flex-1 items-center">
            <Logo />
          </div>

          
          <div className="flex items-center">
            <Link
              href="/contact" // Link to the Contact Us page
              className="btn-sm bg-gradient-to-t from-indigo-600 to-indigo-500 text-white py-2 px-4 rounded hover:bg-gradient-to-b"
            >
              Schedule Demo
            </Link>
          </div>
        </div> */}
      </div> 
    </header>
  );
}
