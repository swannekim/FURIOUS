import React from 'react'
import TestComp from './components/TestComp'

const HomePage = () => {

  /* fetch data from URL or Endpoint */
  // fetch('http://localhost:8080/api/home')
  // const testres = await fetch('http://127.0.0.1:8080/test');

  return (
    <div className="relative min-h-screen">
      <header className="w-full p-5 shadow-lg glass rounded-xl backdrop-blur-md bg-opacity-30 mb-4">
        <div className="container ml-2">
          <h1 className="text-2xl font-bold">FURIOUS: Fully Unified Risk-assessment with Interactive Operational User System for vessels</h1>
          <h3 className="text-zinc-400 font-light">swannekim@snu.ac.kr &nbsp; williamkim10@snu.ac.kr</h3>
        </div>
      </header>
      <div className="flex flex-col items-center justify-center min-h-screen mb-0">
        <TestComp />
      </div>
      <footer className="footer footer-center bg-base-300 text-base-content p-4">
        <aside>
          <p>Copyright © {new Date().getFullYear()} - All right reserved by SNU ViBA Lab. & KRISO</p>
        </aside>
      </footer>
    </div>
  )
}

export default HomePage